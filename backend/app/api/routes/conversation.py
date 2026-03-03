"""WebSocket endpoint for browser-based conversations."""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import uuid4, UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.websocket import connection_manager
from app.models import Agent, Conversation, ConversationMessage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["conversation"])


@router.websocket("/ws/talk-to-agent/{agent_id}")
async def websocket_conversation(
    websocket: WebSocket,
    agent_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    """
    WebSocket endpoint for browser-based conversations with agents.
    
    - Accepts audio chunks from browser
    - Buffers audio until threshold is reached
    - Processes audio through AI pipeline
    - Sends responses back to browser
    
    Args:
        websocket: FastAPI WebSocket connection
        agent_id: UUID string of the agent to talk to
        db: Async database session
    """
    conversation_id = str(uuid4())
    conversation = None
    
    try:
        # ── Validation ──────────────────────────────────────────
        
        # Validate agent_id is UUID format
        try:
            agent_uuid = UUID(agent_id)
        except ValueError:
            await websocket.accept()
            await websocket.send_json({
                "type": "error",
                "message": f"Invalid agent ID format: {agent_id}"
            })
            await websocket.close()
            logger.error(f"Invalid agent ID format: {agent_id}")
            return
        
        # Query agent from database
        from sqlalchemy import select
        stmt = select(Agent).where(Agent.id == agent_uuid)
        result = await db.execute(stmt)
        agent = result.scalar_one_or_none()
        
        if not agent:
            await websocket.accept()
            await websocket.send_json({
                "type": "error",
                "message": f"Agent not found: {agent_id}"
            })
            await websocket.close()
            logger.error(f"Agent not found: {agent_id}")
            return
        
        # ── Connection Setup ────────────────────────────────────
        
        await connection_manager.connect(websocket, conversation_id)
        logger.info(f"Conversation started: {conversation_id} with agent {agent_id}")
        
        # Send connection confirmation
        await connection_manager.send_json(
            conversation_id,
            {
                "type": "connected",
                "conversation_id": conversation_id,
                "agent_name": agent.name,
                "message": f"Connected to {agent.name}. Start speaking!"
            }
        )
        
        # ── Create Conversation Record ──────────────────────────
        
        try:
            conversation = Conversation(
                company_id=agent.company_id,
                agent_id=agent.id,
                channel="browser",
                status="active",
                started_at=datetime.utcnow().isoformat(),
                enable_recording=agent.call_settings.get("enableRecording", True),
                stt_model="whisper",
                llm_model="gpt-4",
                tts_model=agent.voice_settings.get("provider", "elevenlabs")
            )
            db.add(conversation)
            await db.flush()  # Get conversation ID
            logger.info(f"Conversation record created: {conversation.id}")
        except Exception as e:
            logger.error(f"Error creating conversation record: {str(e)}")
            await connection_manager.send_json(
                conversation_id,
                {
                    "type": "error",
                    "message": "Failed to create conversation record"
                }
            )
            connection_manager.disconnect(conversation_id)
            return
        
        # ── Audio Buffering & Processing ───────────────────────
        
        audio_buffer = b""
        buffer_threshold = 32000  # ~2 seconds at 16kHz
        
        while True:
            try:
                # Receive audio chunk from client
                audio_chunk = await connection_manager.receive_bytes(conversation_id)
                
                if audio_chunk is None:
                    # Client disconnected
                    logger.info(f"Client disconnected: {conversation_id}")
                    break
                
                # Add to buffer
                audio_buffer += audio_chunk
                
                # Check if buffer threshold reached
                if len(audio_buffer) >= buffer_threshold:
                    # Send status update
                    await connection_manager.send_json(
                        conversation_id,
                        {
                            "type": "status",
                            "message": "Processing audio...",
                            "processing": True
                        }
                    )
                    
                    # TODO: Process audio through Whisper -> GPT-4 -> ElevenLabs
                    # For now, send placeholder response
                    logger.info(f"Processing audio chunk: {len(audio_buffer)} bytes")
                    
                    # Save placeholder user message to DB
                    user_message = ConversationMessage(
                        conversation_id=conversation.id,
                        speaker="user",
                        message="[Audio received]",
                        timestamp=datetime.utcnow().isoformat()
                    )
                    db.add(user_message)
                    
                    # Send placeholder transcript
                    await connection_manager.send_json(
                        conversation_id,
                        {
                            "type": "transcript",
                            "speaker": "user",
                            "text": "[Audio processing...]"
                        }
                    )
                    
                    # Reset buffer
                    audio_buffer = b""
                    
                    await db.commit()
                    
            except Exception as e:
                logger.error(f"Error processing audio: {str(e)}")
                await connection_manager.send_json(
                    conversation_id,
                    {
                        "type": "error",
                        "message": f"Error processing audio: {str(e)}"
                    }
                )
                break
        
        # ── Cleanup ─────────────────────────────────────────────
        
        if conversation:
            conversation.status = "completed"
            conversation.ended_at = datetime.utcnow().isoformat()
            await db.commit()
            logger.info(f"Conversation {conversation.id} completed")
        
        connection_manager.disconnect(conversation_id)
        logger.info(f"WebSocket connection closed: {conversation_id}")
        
    except WebSocketDisconnect:
        connection_manager.disconnect(conversation_id)
        logger.info(f"WebSocket disconnected: {conversation_id}")
        if conversation:
            conversation.status = "completed"
            conversation.ended_at = datetime.utcnow().isoformat()
            try:
                await db.commit()
            except Exception as e:
                logger.error(f"Error updating conversation on disconnect: {str(e)}")
        
    except Exception as e:
        logger.error(f"Unexpected error in websocket_conversation: {str(e)}")
        connection_manager.disconnect(conversation_id)
        if conversation:
            conversation.status = "failed"
            conversation.error_message = str(e)
            conversation.ended_at = datetime.utcnow().isoformat()
            try:
                await db.commit()
            except Exception as db_err:
                logger.error(f"Error updating conversation on error: {str(db_err)}")
        try:
            await connection_manager.send_json(
                conversation_id,
                {
                    "type": "error",
                    "message": "Internal server error"
                }
            )
        except Exception:
            pass  # Connection may already be closed
