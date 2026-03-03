"""
Export routes: Excel, Google Sheets, CSV, scheduled exports.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_id, get_current_active_user
from app.core.database import get_db
from app.models.export import ExportHistory, ScheduledExport
from app.models.user import User
from app.schemas.export import (
    ExcelExportRequest,
    ExportHistoryResponse,
    ExportResponse,
    ScheduledExportCreate,
    ScheduledExportResponse,
    SheetsExportRequest,
)

router = APIRouter(prefix="/export", tags=["Export"])


@router.post("/excel", response_model=ExportResponse, status_code=202)
async def export_to_excel(
    body: ExcelExportRequest,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Export extracted data to Excel."""
    history = ExportHistory(
        company_id=company_id,
        export_type="manual",
        destination="excel",
        call_ids=[str(c) for c in body.call_ids],
        status="processing",
    )
    db.add(history)
    await db.flush()

    from app.worker.tasks import export_to_excel_task

    export_to_excel_task.delay(
        str(history.id),
        [str(c) for c in body.call_ids],
        body.template,
        body.filename,
    )

    return ExportResponse(
        job_id=history.id,
        status="processing",
        estimated_completion_time=30,
    )


@router.post("/sheets", response_model=ExportResponse, status_code=202)
async def export_to_sheets(
    body: SheetsExportRequest,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Export extracted data to Google Sheets."""
    history = ExportHistory(
        company_id=company_id,
        export_type="manual",
        destination="sheets",
        call_ids=[str(c) for c in body.call_ids],
        status="processing",
    )
    db.add(history)
    await db.flush()

    from app.worker.tasks import export_to_sheets_task

    export_to_sheets_task.delay(
        str(history.id),
        [str(c) for c in body.call_ids],
        body.spreadsheet_id,
        body.template,
        body.share_with,
    )

    return ExportResponse(
        job_id=history.id,
        status="processing",
        estimated_completion_time=15,
    )


@router.post("/schedule", response_model=ScheduledExportResponse, status_code=201)
async def create_scheduled_export(
    body: ScheduledExportCreate,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_active_user),
):
    """Create a scheduled export job."""
    sched = ScheduledExport(
        company_id=company_id,
        agent_id=body.agent_id,
        created_by=user.id,
        name=body.name,
        description=body.description,
        frequency=body.frequency,
        scheduled_time=body.scheduled_time,
        days_of_week=body.days_of_week,
        day_of_month=body.day_of_month,
        destination=body.destination,
        destination_config=body.destination_config,
        template_name=body.template,
        columns_to_export=body.columns_to_export,
        filters=body.filters,
    )
    db.add(sched)
    await db.flush()
    return ScheduledExportResponse.model_validate(sched)


@router.get("/schedules", response_model=list[ScheduledExportResponse])
async def list_scheduled_exports(
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """List all scheduled exports for the company."""
    result = await db.execute(
        select(ScheduledExport)
        .where(ScheduledExport.company_id == company_id)
        .order_by(ScheduledExport.created_at.desc())
    )
    return [ScheduledExportResponse.model_validate(s) for s in result.scalars().all()]


@router.delete("/schedule/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    result = await db.execute(
        select(ScheduledExport).where(
            ScheduledExport.id == schedule_id, ScheduledExport.company_id == company_id
        )
    )
    sched = result.scalar_one_or_none()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    await db.delete(sched)


@router.get("/history", response_model=list[ExportHistoryResponse])
async def list_export_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """List export history entries."""
    result = await db.execute(
        select(ExportHistory)
        .where(ExportHistory.company_id == company_id)
        .order_by(ExportHistory.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    return [ExportHistoryResponse.model_validate(e) for e in result.scalars().all()]


@router.get("/csv")
async def export_to_csv(
    call_ids: Optional[str] = Query(None, description="Comma-separated call UUIDs to include"),
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Export extracted data to CSV and return as a downloadable file."""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    from app.models.extraction import ExtractedCallData

    query = select(ExtractedCallData).where(ExtractedCallData.company_id == company_id)

    if call_ids:
        ids = [UUID(c.strip()) for c in call_ids.split(",") if c.strip()]
        if ids:
            query = query.where(ExtractedCallData.call_id.in_(ids))

    result = await db.execute(query.order_by(ExtractedCallData.created_at.desc()))
    items = result.scalars().all()

    if not items:
        raise HTTPException(status_code=404, detail="No extracted data found")

    # Collect all unique keys from extracted_data dicts (dict preserves insertion order in Python 3.7+)
    all_keys: dict[str, None] = {}
    for f in ["call_id", "agent_id", "created_at", "confidence_score", "extraction_method"]:
        all_keys[f] = None
    for item in items:
        for k in (item.extracted_data or {}).keys():
            all_keys[k] = None

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(all_keys), extrasaction="ignore")
    writer.writeheader()
    for item in items:
        row: dict = {
            "call_id": str(item.call_id),
            "agent_id": str(item.agent_id),
            "created_at": str(item.created_at),
            "confidence_score": item.confidence_score,
            "extraction_method": item.extraction_method,
            **(item.extracted_data or {}),
        }
        writer.writerow(row)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="export.csv"'},
    )
