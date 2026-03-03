"""
Call management routes: list, create (outbound), get, get transcript, download recording.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_id, get_current_active_user
from app.core.database import get_db
from app.models.call import Call, CallTranscript
from app.models.user import User
from app.schemas.call import CallCreate, CallListResponse, CallResponse, TranscriptResponse

router = APIRouter(prefix="/calls", tags=["Calls"])


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


@router.get("/{call_id}/recording")
async def download_recording(
    call_id: UUID,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Download or stream the recording for a call."""
    from app.core.config import get_settings

    settings = get_settings()

    result = await db.execute(
        select(Call).where(Call.id == call_id, Call.company_id == company_id)
    )
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    # If we have an S3 key, generate a presigned URL and redirect (non-blocking)
    if call.recording_s3_key:
        try:
            import asyncio
            import boto3

            def _presign():
                s3 = boto3.client(
                    "s3",
                    endpoint_url=settings.S3_ENDPOINT,
                    aws_access_key_id=settings.S3_ACCESS_KEY,
                    aws_secret_access_key=settings.S3_SECRET_KEY,
                    region_name=settings.S3_REGION,
                )
                return s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": settings.S3_BUCKET_RECORDINGS, "Key": call.recording_s3_key},
                    ExpiresIn=3600,
                )

            presigned_url = await asyncio.get_event_loop().run_in_executor(None, _presign)
            from fastapi.responses import RedirectResponse

            return RedirectResponse(url=presigned_url)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Could not retrieve recording: {str(e)}")

    # Fall back to redirecting to the Twilio recording URL
    if call.recording_url:
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url=call.recording_url)

    raise HTTPException(status_code=404, detail="No recording available for this call")
