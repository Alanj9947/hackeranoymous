"""Export schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ExcelExportRequest(BaseModel):
    call_ids: List[UUID]
    template: str = "customer_service_summary"
    include_charts: bool = False
    filename: Optional[str] = None


class SheetsExportRequest(BaseModel):
    call_ids: List[UUID]
    spreadsheet_id: Optional[str] = None  # None = create new
    action: str = "append"  # append, create_new
    template: str = "customer_service_summary"
    share_with: Optional[List[str]] = None


class ScheduledExportCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    frequency: str  # daily, weekly, monthly
    scheduled_time: str = "09:00"  # HH:MM
    days_of_week: Optional[List[int]] = None
    day_of_month: Optional[int] = None
    template: str = "customer_service_summary"
    destination: str  # excel, sheets, csv
    destination_config: Optional[Dict[str, Any]] = None
    columns_to_export: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    agent_id: Optional[UUID] = None


class ScheduledExportResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    frequency: str
    scheduled_time: Optional[str] = None
    destination: str
    template_name: Optional[str] = None
    enabled: bool = True
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    last_run_status: Optional[str] = None
    run_count: int = 0
    created_at: Any = None

    model_config = {"from_attributes": True}


class ExportResponse(BaseModel):
    job_id: UUID
    status: str
    estimated_completion_time: Optional[int] = None
    download_url: Optional[str] = None
    spreadsheet_url: Optional[str] = None
    rows_exported: Optional[int] = None


class ExportHistoryResponse(BaseModel):
    id: UUID
    export_type: str
    destination: str
    rows_exported: Optional[int] = None
    file_path: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: Any = None

    model_config = {"from_attributes": True}
