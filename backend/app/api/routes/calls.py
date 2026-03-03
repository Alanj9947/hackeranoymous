"""
Call management routes: list, create (outbound), get, get transcript.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
