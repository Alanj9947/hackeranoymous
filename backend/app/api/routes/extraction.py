"""
Data extraction routes: trigger, status, list, review.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_id, get_current_active_user
from app.core.database import get_db
from app.models.call import Call
from app.models.extraction import DataExtractionJob, ExtractedCallData
from app.models.user import User
from app.schemas.extraction import (
    ExtractedDataListResponse,
    ExtractedDataResponse,
    ExtractionReviewRequest,
    ExtractionTriggerResponse,
)

router = APIRouter(prefix="/extract-data", tags=["Data Extraction"])


@router.post("/{call_id}", response_model=ExtractionTriggerResponse, status_code=202)
async def trigger_extraction(
    call_id: UUID,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Trigger data extraction for a specific call."""
    # Verify call
    call_result = await db.execute(
        select(Call).where(Call.id == call_id, Call.company_id == company_id)
    )
    call = call_result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    # Check if already extracted
    existing = await db.execute(
        select(ExtractedCallData).where(ExtractedCallData.call_id == call_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Data already extracted for this call")

    # Create job
    job = DataExtractionJob(
        call_id=call_id,
        company_id=company_id,
        status="queued",
    )
    db.add(job)
    await db.flush()

    # Queue async task
    from app.worker.tasks import process_extraction

    process_extraction.delay(str(job.id))

    return ExtractionTriggerResponse(
        job_id=job.id,
        call_id=call_id,
        status="queued",
        estimated_wait_time=5,
        message="Extraction job queued",
    )


@router.get("/{call_id}", response_model=ExtractedDataResponse)
async def get_extraction(
    call_id: UUID,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Get extraction results for a call."""
    result = await db.execute(
        select(ExtractedCallData).where(
            ExtractedCallData.call_id == call_id,
            ExtractedCallData.company_id == company_id,
        )
    )
    data = result.scalar_one_or_none()
    if not data:
        raise HTTPException(status_code=404, detail="Extraction not found")
    return ExtractedDataResponse.model_validate(data)


@router.get("", response_model=ExtractedDataListResponse)
async def list_extractions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    agent_id: Optional[UUID] = None,
    reviewed: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """List all extractions for the company."""
    query = select(ExtractedCallData).where(ExtractedCallData.company_id == company_id)
    count_q = (
        select(func.count())
        .select_from(ExtractedCallData)
        .where(ExtractedCallData.company_id == company_id)
    )

    if agent_id:
        query = query.where(ExtractedCallData.agent_id == agent_id)
        count_q = count_q.where(ExtractedCallData.agent_id == agent_id)
    if reviewed is not None:
        query = query.where(ExtractedCallData.reviewed == reviewed)
        count_q = count_q.where(ExtractedCallData.reviewed == reviewed)

    query = query.order_by(ExtractedCallData.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    items = (await db.execute(query)).scalars().all()
    total = (await db.execute(count_q)).scalar()

    return ExtractedDataListResponse(
        items=[ExtractedDataResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.put("/{call_id}/review", response_model=ExtractedDataResponse)
async def review_extraction(
    call_id: UUID,
    body: ExtractionReviewRequest,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_active_user),
):
    """Approve or reject extracted data."""
    result = await db.execute(
        select(ExtractedCallData).where(
            ExtractedCallData.call_id == call_id,
            ExtractedCallData.company_id == company_id,
        )
    )
    data = result.scalar_one_or_none()
    if not data:
        raise HTTPException(status_code=404, detail="Extraction not found")

    from datetime import datetime, timezone

    data.reviewed = True
    data.reviewed_by = user.id
    data.approved = body.approved
    data.quality_comments = body.comments
    await db.flush()

    return ExtractedDataResponse.model_validate(data)
