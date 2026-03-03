"""PhoneCallService - Manage phone call lifecycle and routing."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.call import Call, CallTranscript
from app.models.agent import Agent
from app.models.phone_number import PhoneNumber

logger = logging.getLogger(__name__)


class PhoneCallService:
    """Handle phone call lifecycle: creation, routing, updates, completion."""

    @staticmethod
    async def create_inbound_call(
        db: AsyncSession,
        twilio_call_sid: str,
        from_number: str,
        to_number: str,
    ) -> tuple[Optional[Call], Optional[Agent], Optional[str]]:
        """
        Create a new inbound call record and find the assigned agent.

        Args:
            db: Database session
            twilio_call_sid: Twilio call SID
            from_number: Caller's phone number (E.164)
            to_number: Called phone number (E.164)

        Returns:
            Tuple of (Call, Agent, error_message)
            - Call: Created call record (may be None if error)
            - Agent: Assigned agent (may be None if not found)
            - error_message: Error string if any (None if success)
        """
        try:
            # Find phone number and assigned agent
            result = await db.execute(
                select(PhoneNumber).where(
                    PhoneNumber.phone_number == to_number,
                    PhoneNumber.status == "active",
                    PhoneNumber.inbound_enabled == True,
                )
            )
            phone_number = result.scalar_one_or_none()

            if not phone_number:
                logger.warning(
                    f"Inbound call to unmapped number: {to_number}",
                    extra={"call_sid": twilio_call_sid},
                )
                return None, None, f"No agent assigned to {to_number}"

            if not phone_number.agent_id:
                logger.warning(
                    f"Phone number has no agent assigned: {to_number}",
                    extra={"call_sid": twilio_call_sid},
                )
                return None, None, "No agent assigned to this number"

            # Get the agent
            result = await db.execute(select(Agent).where(Agent.id == phone_number.agent_id))
            agent = result.scalar_one_or_none()

            if not agent or agent.status != "active":
                logger.warning(
                    f"Agent not active for number: {to_number}",
                    extra={"call_sid": twilio_call_sid},
                )
                return None, None, "Agent is not available"

            # Create call record
            call = Call(
                company_id=agent.company_id,
                agent_id=agent.id,
                twilio_call_sid=twilio_call_sid,
                direction="inbound",
                from_number=from_number,
                to_number=to_number,
                status="initiated",
            )
            db.add(call)
            await db.flush()

            logger.info(
                f"Inbound call created: {call.id}",
                extra={
                    "call_sid": twilio_call_sid,
                    "from": from_number,
                    "to": to_number,
                    "agent_id": str(agent.id),
                },
            )

            return call, agent, None

        except Exception as e:
            logger.error(
                f"Error creating inbound call: {str(e)}",
                extra={"call_sid": twilio_call_sid},
                exc_info=True,
            )
            return None, None, f"Internal error: {str(e)}"

    @staticmethod
    async def update_call_status(
        db: AsyncSession,
        twilio_call_sid: str,
        status: str,
        duration_seconds: Optional[int] = None,
        recording_url: Optional[str] = None,
    ) -> bool:
        """
        Update call status from Twilio webhook.

        Args:
            db: Database session
            twilio_call_sid: Twilio call SID
            status: Call status (ringing, in-progress, completed, failed, etc.)
            duration_seconds: Call duration if available
            recording_url: Recording URL if available

        Returns:
            True if updated, False if call not found
        """
        try:
            result = await db.execute(
                select(Call).where(Call.twilio_call_sid == twilio_call_sid)
            )
            call = result.scalar_one_or_none()

            if not call:
                logger.warning(f"Status update for unknown call: {twilio_call_sid}")
                return False

            call.status = status

            if duration_seconds:
                call.duration_seconds = duration_seconds

            if recording_url:
                call.recording_url = recording_url

            # Mark as ended if call is complete
            if status in ("completed", "failed", "no-answer", "busy", "canceled"):
                call.ended_at = datetime.now(timezone.utc).isoformat()

            await db.commit()

            logger.info(
                f"Call status updated: {call.id} → {status}",
                extra={
                    "call_sid": twilio_call_sid,
                    "duration": duration_seconds,
                },
            )

            return True

        except Exception as e:
            logger.error(
                f"Error updating call status: {str(e)}",
                extra={"call_sid": twilio_call_sid},
                exc_info=True,
            )
            return False

    @staticmethod
    async def save_call_transcript(
        db: AsyncSession,
        call_id: UUID,
        full_text: str,
        segments: list,
    ) -> bool:
        """
        Save call transcript to database.

        Args:
            db: Database session
            call_id: Call ID
            full_text: Full conversation text
            segments: List of message segments with speaker, text, timing

        Returns:
            True if saved, False on error
        """
        try:
            # Check if transcript already exists
            result = await db.execute(
                select(CallTranscript).where(CallTranscript.call_id == call_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.info(f"Transcript already exists for call: {call_id}")
                return True

            # Create new transcript
            transcript = CallTranscript(
                call_id=call_id,
                full_text=full_text,
                segments=segments,
                word_count=len(full_text.split()) if full_text else 0,
                language="en",
            )
            db.add(transcript)
            await db.commit()

            logger.info(
                f"Transcript saved: {call_id}",
                extra={"words": transcript.word_count},
            )

            return True

        except Exception as e:
            logger.error(
                f"Error saving transcript: {str(e)}",
                extra={"call_id": str(call_id)},
                exc_info=True,
            )
            return False

    @staticmethod
    async def get_call_details(
        db: AsyncSession,
        call_id: UUID,
    ) -> Optional[dict]:
        """
        Get full call details including agent and transcript.

        Args:
            db: Database session
            call_id: Call ID

        Returns:
            Call details dict or None if not found
        """
        try:
            result = await db.execute(select(Call).where(Call.id == call_id))
            call = result.scalar_one_or_none()

            if not call:
                return None

            return {
                "id": str(call.id),
                "twilio_call_sid": call.twilio_call_sid,
                "agent_id": str(call.agent_id),
                "agent_name": call.agent.name if call.agent else None,
                "direction": call.direction,
                "from_number": call.from_number,
                "to_number": call.to_number,
                "status": call.status,
                "duration_seconds": call.duration_seconds,
                "started_at": call.started_at,
                "ended_at": call.ended_at,
                "recording_url": call.recording_url,
                "stt_model": call.stt_model,
                "llm_model": call.llm_model,
                "tts_model": call.tts_model,
                "ai_cost_usd": call.ai_cost_usd,
                "transcript": {
                    "full_text": call.transcript.full_text if call.transcript else None,
                    "segments": call.transcript.segments if call.transcript else None,
                    "word_count": call.transcript.word_count if call.transcript else None,
                }
                if call.transcript
                else None,
            }

        except Exception as e:
            logger.error(
                f"Error getting call details: {str(e)}",
                extra={"call_id": str(call_id)},
                exc_info=True,
            )
            return None

    @staticmethod
    async def update_phone_number_stats(
        db: AsyncSession,
        to_number: str,
        call_completed: bool = True,
    ) -> bool:
        """
        Update phone number statistics after call.

        Args:
            db: Database session
            to_number: Phone number called
            call_completed: Whether call was successfully completed

        Returns:
            True if updated, False on error
        """
        try:
            result = await db.execute(
                select(PhoneNumber).where(PhoneNumber.phone_number == to_number)
            )
            phone_number = result.scalar_one_or_none()

            if not phone_number:
                return False

            phone_number.call_count = (phone_number.call_count or 0) + 1
            if call_completed:
                phone_number.last_call_at = datetime.now(timezone.utc).isoformat()

            await db.commit()

            logger.info(
                f"Phone number stats updated: {to_number} (calls: {phone_number.call_count})"
            )

            return True

        except Exception as e:
            logger.error(
                f"Error updating phone number stats: {str(e)}",
                extra={"phone_number": to_number},
                exc_info=True,
            )
            return False
