"""
WebSocket handler for Twilio media streams.
Processes real-time audio: STT → LLM → TTS → send back.
"""

from __future__ import annotations

import asyncio
import base64
import json
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.services.voice.stt import transcribe_audio_chunk
from app.services.voice.llm import get_llm_response
from app.services.voice.tts import synthesize_speech

logger = get_logger(__name__)


async def media_stream_ws(websocket: WebSocket, call_id: str):
    """
    Handle Twilio media stream WebSocket connection.
    Receives audio → STT → LLM → TTS → send audio back in real-time.
    """
    await websocket.accept()
    logger.info("media_stream_connected", call_id=call_id)

    stream_sid = None
    audio_buffer = bytearray()
    conversation_history = []
    agent_config = None

    try:
        # Load agent config
        from app.core.database import async_session_factory
        from app.models.call import Call
        from app.models.agent import Agent
        from sqlalchemy import select

        async with async_session_factory() as db:
            result = await db.execute(select(Call).where(Call.id == UUID(call_id)))
            call = result.scalar_one_or_none()
            if call:
                agent_result = await db.execute(select(Agent).where(Agent.id == call.agent_id))
                agent = agent_result.scalar_one_or_none()
                if agent:
                    agent_config = {
                        "system_prompt": agent.system_prompt,
                        "voice_settings": agent.voice_settings,
                        "call_settings": agent.call_settings,
                    }
                    # Send first message if configured
                    first_msg = agent.system_prompt.get("firstMessage", "")
                    if first_msg:
                        conversation_history.append({"role": "assistant", "content": first_msg})

        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("event") == "connected":
                logger.info("stream_connected", call_id=call_id)

            elif msg.get("event") == "start":
                stream_sid = msg["start"]["streamSid"]
                logger.info("stream_started", stream_sid=stream_sid, call_id=call_id)

            elif msg.get("event") == "media":
                # Accumulate audio chunks
                payload = base64.b64decode(msg["media"]["payload"])
                audio_buffer.extend(payload)

                # Process when we have enough audio (~ 2 seconds of 8kHz mulaw)
                if len(audio_buffer) >= 16000:
                    audio_data = bytes(audio_buffer)
                    audio_buffer.clear()

                    # STT: Convert audio to text
                    transcript = await transcribe_audio_chunk(audio_data)
                    if transcript and transcript.strip():
                        logger.info("user_speech", text=transcript[:100], call_id=call_id)
                        conversation_history.append({"role": "user", "content": transcript})

                        # LLM: Get AI response
                        system_prompt = ""
                        if agent_config:
                            sp = agent_config["system_prompt"]
                            system_prompt = f"""You are {sp.get('personality', 'a helpful assistant')}.
Your goals: {', '.join(sp.get('goals', []))}
Tone: {sp.get('tone', 'professional')}
Language: {sp.get('language', 'en')}
Constraints: {', '.join(sp.get('constraints', []))}"""

                        ai_response = await get_llm_response(
                            system_prompt=system_prompt,
                            conversation_history=conversation_history,
                        )

                        if ai_response:
                            conversation_history.append(
                                {"role": "assistant", "content": ai_response}
                            )

                            # TTS: Convert text to audio
                            voice_id = None
                            tts_provider = "elevenlabs"
                            if agent_config:
                                vs = agent_config["voice_settings"]
                                voice_id = vs.get("voiceId")
                                tts_provider = vs.get("provider", "elevenlabs")

                            audio_response = await synthesize_speech(
                                text=ai_response,
                                provider=tts_provider,
                                voice_id=voice_id,
                            )

                            if audio_response and stream_sid:
                                # Send audio back to Twilio
                                audio_b64 = base64.b64encode(audio_response).decode()
                                media_msg = {
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {"payload": audio_b64},
                                }
                                await websocket.send_text(json.dumps(media_msg))

            elif msg.get("event") == "stop":
                logger.info("stream_stopped", call_id=call_id)
                # Save transcript
                full_transcript = "\n".join(
                    f"{'Agent' if m['role'] == 'assistant' else 'Customer'}: {m['content']}"
                    for m in conversation_history
                    if m.get("content")
                )
                if full_transcript:
                    await _save_transcript(call_id, full_transcript, conversation_history)
                break

    except WebSocketDisconnect:
        logger.info("media_stream_disconnected", call_id=call_id)
    except Exception as e:
        logger.error("media_stream_error", call_id=call_id, error=str(e))
    finally:
        logger.info("media_stream_closed", call_id=call_id)


async def _save_transcript(call_id: str, full_text: str, segments: list):
    """Save the conversation transcript to the database."""
    from app.core.database import async_session_factory
    from app.models.call import CallTranscript

    try:
        async with async_session_factory() as db:
            transcript = CallTranscript(
                call_id=UUID(call_id),
                full_text=full_text,
                segments=segments,
                word_count=len(full_text.split()),
            )
            db.add(transcript)
            await db.commit()
            logger.info("transcript_saved", call_id=call_id, words=transcript.word_count)
    except Exception as e:
        logger.error("transcript_save_error", call_id=call_id, error=str(e))
