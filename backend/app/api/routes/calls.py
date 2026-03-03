"""
Call management routes: list, create (outbound), get, get transcript.
Includes recording management and streaming.
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_id, get_current_active_user
from app.core.database import get_db
from app.core.config import get_settings
from app.models.call import Call, CallTranscript
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.call import CallCreate, CallListResponse, CallResponse, TranscriptResponse
from app.services.call_recording_service import CallRecordingService
from starlette.responses import StreamingResponse

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/calls", tags=["Calls"])

# Initialize recording service
try:
    recording_service = CallRecordingService(
        storage_path=getattr(settings, "RECORDINGS_PATH", "/tmp/recordings")
    )
except Exception as e:
    logger.error(f"Failed to initialize recording service: {str(e)}")
    recording_service = None


@router.get("", response_model=CallListResponse)
async def list_calls(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    agent_id: Optional[UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    direction: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """List calls for the current company, with filters."""
    query = select(Call).where(Call.company_id == company_id)
    count_q = select(func.count()).select_from(Call).where(Call.company_id == company_id)

    if agent_id:
        query = query.where(Call.agent_id == agent_id)
        count_q = count_q.where(Call.agent_id == agent_id)
    if status_filter:
        query = query.where(Call.status == status_filter)
        count_q = count_q.where(Call.status == status_filter)
    if direction:
        query = query.where(Call.direction == direction)
        count_q = count_q.where(Call.direction == direction)

    query = query.order_by(Call.created_at.desc()).offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    calls = result.scalars().all()
    total = (await db.execute(count_q)).scalar()

    return CallListResponse(
        calls=[CallResponse.model_validate(c) for c in calls],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
async def initiate_call(
    body: CallCreate,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Initiate an outbound call via Twilio."""
    from app.services.twilio_service import TwilioService

    twilio_svc = TwilioService()

    call = Call(
        company_id=company_id,
        agent_id=body.agent_id,
        direction=body.direction,
        to_number=body.to_number,
        from_number=twilio_svc.phone_number,
        status="initiated",
        metadata_json=body.metadata_json,
    )
    db.add(call)
    await db.flush()

    # Fire outbound call via Twilio (async task)
    from app.worker.tasks import initiate_outbound_call

    initiate_outbound_call.delay(str(call.id))

    return CallResponse.model_validate(call)


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: UUID,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Get a single call."""
    result = await db.execute(
        select(Call).where(Call.id == call_id, Call.company_id == company_id)
    )
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return CallResponse.model_validate(call)


@router.get("/{call_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(
    call_id: UUID,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Get the transcript for a call."""
    # Verify call belongs to company
    call_result = await db.execute(
        select(Call).where(Call.id == call_id, Call.company_id == company_id)
    )
    if not call_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Call not found")

    result = await db.execute(select(CallTranscript).where(CallTranscript.call_id == call_id))
    transcript = result.scalar_one_or_none()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not available yet")
    return TranscriptResponse.model_validate(transcript)


# ── Recording Management Endpoints ──────────────────────────────────

@router.get("/{call_id}/recording")
async def get_call_recording(
    call_id: str,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
    range_header: Optional[str] = Header(None),
):
    """
    Download or stream call recording (for Conversation/browser calls).

    Args:
        call_id: Conversation ID
        range_header: HTTP Range header for partial content
    """
    if not recording_service:
        raise HTTPException(status_code=503, detail="Recording service unavailable")

    try:
        # Validate call_id is UUID format
        try:
            conversation_id = UUID(call_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid call ID format")

        # Check if conversation exists and belongs to company
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.company_id == company_id,
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            logger.warning(f"Conversation not found: {call_id}")
            raise HTTPException(status_code=404, detail="Conversation not found")

        if not conversation.recording_url:
            logger.warning(f"No recording for conversation: {call_id}")
            raise HTTPException(status_code=404, detail="No recording available")

        # Get recording from storage
        audio_data = await recording_service.get_recording(
            conversation_id,
            format="mp3",
        )

        if not audio_data:
            logger.warning(f"Recording file not found: {call_id}")
            raise HTTPException(status_code=404, detail="Recording file not found")

        # Handle range requests for seeking
        if range_header:
            logger.info(f"Range request: {range_header}")
            try:
                ranges = range_header.replace("bytes=", "").split(",")
                start, end = ranges[0].split("-")
                start = int(start) if start else 0
                end = int(end) if end else len(audio_data) - 1

                if start < 0 or end >= len(audio_data) or start > end:
                    raise ValueError("Invalid range")

                partial_data = audio_data[start : end + 1]
                return StreamingResponse(
                    iter([partial_data]),
                    status_code=206,
                    media_type="audio/mpeg",
                    headers={
                        "Content-Range": f"bytes {start}-{end}/{len(audio_data)}",
                        "Accept-Ranges": "bytes",
                        "Content-Length": str(len(partial_data)),
                    },
                )
            except Exception as e:
                logger.warning(f"Invalid range header: {str(e)}")

        # Return full file
        return StreamingResponse(
            iter([audio_data]),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename=call-{call_id}.mp3",
                "Content-Length": str(len(audio_data)),
                "Accept-Ranges": "bytes",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving recording: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving recording")


@router.get("/{call_id}/info")
async def get_call_info(
    call_id: str,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Get metadata about a call including recording status."""
    try:
        try:
            conversation_id = UUID(call_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid call ID format")

        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.company_id == company_id,
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        recording_info = None
        if conversation.recording_url and recording_service:
            recording_info = await recording_service.get_recording_info(
                conversation_id,
                format="mp3",
            )

        return {
            "id": str(conversation.id),
            "agent_id": str(conversation.agent_id),
            "duration_seconds": conversation.duration_seconds,
            "status": conversation.status,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "started_at": conversation.started_at,
            "ended_at": conversation.ended_at,
            "transcript": conversation.transcript,
            "sentiment": conversation.sentiment,
            "recording": recording_info,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting call info: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving call information")


@router.delete("/{call_id}/recording")
async def delete_call_recording(
    call_id: str,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Delete recording for a call."""
    if not recording_service:
        raise HTTPException(status_code=503, detail="Recording service unavailable")

    try:
        try:
            conversation_id = UUID(call_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid call ID format")

        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.company_id == company_id,
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        deleted = await recording_service.delete_recording(conversation_id, format="mp3")

        if not deleted:
            raise HTTPException(status_code=404, detail="Recording not found")

        conversation.recording_url = None
        await db.commit()

        logger.info(f"Recording deleted: {call_id}")
        return {"message": "Recording deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting recording: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting recording")
