"""
PhoneMediaStream - WebSocket handler for Twilio phone call media.
Processes real-time audio: STT → LLM → TTS → send back to phone.
Integrates with Phase 2 ConversationService for full AI pipeline.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.config import get_settings
from app.models.call import Call
from app.models.agent import Agent
from app.services.phone_call_service import PhoneCallService
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)
settings = get_settings()


class PhoneMediaStreamHandler:
    """Handle real-time audio processing for phone calls."""

    def __init__(self, websocket: WebSocket, call_id: str):
        self.websocket = websocket
        self.call_id = call_id
        self.stream_sid = None
        self.audio_buffer = bytearray()
        self.conversation_history = []
        self.agent_config = None
        self.agent_id = None
        self.company_id = None
        self.call_record = None

    async def initialize(self) -> bool:
        """Load call and agent configuration."""
        try:
            async with async_session_factory() as db:
                # Get call record
                from sqlalchemy import select

                result = await db.execute(select(Call).where(Call.id == UUID(self.call_id)))
                self.call_record = result.scalar_one_or_none()

                if not self.call_record:
                    logger.error(f"Call not found: {self.call_id}")
                    return False

                self.agent_id = self.call_record.agent_id
                self.company_id = self.call_record.company_id

                # Get agent configuration
                result = await db.execute(select(Agent).where(Agent.id == self.agent_id))
                agent = result.scalar_one_or_none()

                if not agent:
                    logger.error(f"Agent not found: {self.agent_id}")
                    return False

                self.agent_config = {
                    "name": agent.name,
                    "system_prompt": agent.system_prompt or {},
                    "voice_settings": agent.voice_settings or {},
                }

                logger.info(
                    f"Phone media stream initialized",
                    extra={"call_id": self.call_id, "agent_id": str(self.agent_id)},
                )

                return True

        except Exception as e:
            logger.error(f"Error initializing media stream: {str(e)}", exc_info=True)
            return False

    async def handle(self) -> None:
        """Main handler for media stream WebSocket."""
        try:
            # Initialize
            if not await self.initialize():
                await self._send_error("Failed to initialize call")
                return

            # Process messages
            while True:
                data = await self.websocket.receive_text()
                msg = json.loads(data)

                event = msg.get("event")

                if event == "connected":
                    await self._handle_connected(msg)
                elif event == "start":
                    await self._handle_start(msg)
                elif event == "media":
                    await self._handle_media(msg)
                elif event == "dtmf":
                    await self._handle_dtmf(msg)
                elif event == "stop":
                    await self._handle_stop(msg)
                    break
                else:
                    logger.warning(f"Unknown event: {event}")

        except WebSocketDisconnect:
            logger.info(
                f"Phone media stream disconnected",
                extra={"call_id": self.call_id},
            )
        except Exception as e:
            logger.error(
                f"Phone media stream error: {str(e)}",
                extra={"call_id": self.call_id},
                exc_info=True,
            )
        finally:
            await self._cleanup()

    async def _handle_connected(self, msg: dict) -> None:
        """Handle stream connection event."""
        logger.info(f"Stream connected", extra={"call_id": self.call_id})

    async def _handle_start(self, msg: dict) -> None:
        """Handle stream start event."""
        self.stream_sid = msg.get("start", {}).get("streamSid")
        logger.info(
            f"Stream started",
            extra={"call_id": self.call_id, "stream_sid": self.stream_sid},
        )

    async def _handle_media(self, msg: dict) -> None:
        """Handle media (audio) event."""
        try:
            # Decode audio payload
            payload = base64.b64decode(msg.get("media", {}).get("payload", ""))
            self.audio_buffer.extend(payload)

            # Process when we have enough audio (~2 seconds of 8kHz μ-law = 16KB)
            if len(self.audio_buffer) >= 16000:
                audio_data = bytes(self.audio_buffer)
                self.audio_buffer.clear()

                # Process audio in background
                asyncio.create_task(self._process_audio_chunk(audio_data))

        except Exception as e:
            logger.error(f"Error handling media: {str(e)}", exc_info=True)

    async def _handle_dtmf(self, msg: dict) -> None:
        """Handle DTMF (touch tone) input."""
        digit = msg.get("dtmf", {}).get("digit")
        logger.info(f"DTMF received: {digit}", extra={"call_id": self.call_id})
        # Future: Handle DTMF-based menus

    async def _handle_stop(self, msg: dict) -> None:
        """Handle stream stop event."""
        logger.info(f"Stream stopped", extra={"call_id": self.call_id})

    async def _process_audio_chunk(self, audio_data: bytes) -> None:
        """
        Process audio chunk through full pipeline.
        STT → LLM → TTS → send back
        """
        try:
            async with async_session_factory() as db:
                # Use ConversationService from Phase 2
                service = ConversationService()

                # 1. STT: Transcribe audio
                transcript = await service.transcribe_audio(
                    audio_data=audio_data,
                    model="whisper-1",
                )

                if not transcript or not transcript.strip():
                    logger.debug(f"No speech detected in chunk")
                    return

                logger.info(
                    f"User said: {transcript[:100]}",
                    extra={"call_id": self.call_id},
                )

                # Add to conversation history
                self.conversation_history.append({"role": "user", "content": transcript})

                # Limit history to 20 messages to prevent token overflow
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]

                # 2. LLM: Get AI response
                system_prompt = self._build_system_prompt()

                ai_response = await service.get_llm_response(
                    system_prompt=system_prompt,
                    messages=self.conversation_history,
                    model="gpt-4",
                )

                if not ai_response:
                    logger.warning(f"No LLM response generated")
                    return

                logger.info(
                    f"Agent response: {ai_response[:100]}",
                    extra={"call_id": self.call_id},
                )

                # Add to history
                self.conversation_history.append({"role": "assistant", "content": ai_response})

                # 3. TTS: Synthesize speech
                voice_settings = self.agent_config.get("voice_settings", {})
                voice_id = voice_settings.get("voice_id", "21m00Tcm4TlvDq8ikWAM")  # Default ElevenLabs
                tts_provider = voice_settings.get("provider", "elevenlabs")

                audio_response = await service.synthesize_speech(
                    text=ai_response,
                    provider=tts_provider,
                    voice_id=voice_id,
                )

                if audio_response and self.stream_sid:
                    # 4. Send audio back to caller
                    await self._send_audio(audio_response)

        except Exception as e:
            logger.error(
                f"Error processing audio chunk: {str(e)}",
                extra={"call_id": self.call_id},
                exc_info=True,
            )

    async def _send_audio(self, audio_data: bytes) -> None:
        """Send audio data back to Twilio."""
        try:
            audio_b64 = base64.b64encode(audio_data).decode()
            msg = {
                "event": "media",
                "streamSid": self.stream_sid,
                "media": {"payload": audio_b64},
            }
            await self.websocket.send_text(json.dumps(msg))
        except Exception as e:
            logger.error(f"Error sending audio: {str(e)}")

    async def _send_error(self, error_msg: str) -> None:
        """Send error message back."""
        try:
            msg = {"event": "error", "message": error_msg}
            await self.websocket.send_text(json.dumps(msg))
        except Exception as e:
            logger.error(f"Error sending error message: {str(e)}")

    def _build_system_prompt(self) -> str:
        """Build system prompt from agent config."""
        cfg = self.agent_config.get("system_prompt", {})
        personality = cfg.get("personality", "a helpful assistant")
        goals = cfg.get("goals", [])
        tone = cfg.get("tone", "professional")
        constraints = cfg.get("constraints", [])

        prompt = f"""You are {personality}.

Goals:
{chr(10).join(f'- {g}' for g in goals) if goals else 'Provide helpful assistance'}

Tone: {tone}

Constraints:
{chr(10).join(f'- {c}' for c in constraints) if constraints else 'Be professional and respectful'}

Keep responses concise and natural for phone conversation (40-80 words max).
Speak conversationally, not robotically."""

        return prompt

    async def _cleanup(self) -> None:
        """Cleanup after call ends."""
        try:
            async with async_session_factory() as db:
                # Save transcript
                if self.conversation_history:
                    full_text = "\n".join(
                        f"{'Agent' if m['role'] == 'assistant' else 'Caller'}: {m['content']}"
                        for m in self.conversation_history
                    )

                    await PhoneCallService.save_call_transcript(
                        db=db,
                        call_id=UUID(self.call_id),
                        full_text=full_text,
                        segments=self.conversation_history,
                    )

                # Update call status
                result = await db.execute(
                    select(Call).where(Call.id == UUID(self.call_id))
                )
                call = result.scalar_one_or_none()

                if call:
                    call.status = "completed"
                    call.ended_at = datetime.now(timezone.utc).isoformat()
                    await db.commit()

                # Update phone number stats
                if call:
                    await PhoneCallService.update_phone_number_stats(
                        db=db,
                        to_number=call.to_number,
                        call_completed=True,
                    )

                logger.info(
                    f"Phone call cleanup complete",
                    extra={"call_id": self.call_id},
                )

        except Exception as e:
            logger.error(f"Error in cleanup: {str(e)}", exc_info=True)


# FastAPI WebSocket handler function
async def phone_media_stream_ws(websocket: WebSocket, call_id: str):
    """
    Handle Twilio phone call media stream.
    WebSocket endpoint: /ws/media-stream/{call_id}
    """
    await websocket.accept()
    handler = PhoneMediaStreamHandler(websocket, call_id)
    await handler.handle()
