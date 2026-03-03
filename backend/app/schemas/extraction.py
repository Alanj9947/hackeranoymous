"""Extraction schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class ExtractionTriggerResponse(BaseModel):
    job_id: UUID
    call_id: UUID
    status: str = "queued"
    estimated_wait_time: int = 5
    message: str = "Extraction job queued"


class ExtractedDataResponse(BaseModel):
    id: UUID
    call_id: UUID
    company_id: UUID
    agent_id: UUID
    extraction_method: Optional[str] = None
    model_used: Optional[str] = None
    processing_time_ms: Optional[int] = None
    confidence_score: Optional[float] = None
    extracted_data: Dict[str, Any] = {}
    reviewed: bool = False
    approved: Optional[bool] = None
    quality_comments: Optional[str] = None
    exported: bool = False
    export_destinations: Optional[Dict[str, Any]] = None
    created_at: Any = None

    model_config = {"from_attributes": True}


class ExtractedDataListResponse(BaseModel):
    items: List[ExtractedDataResponse]
    total: int
    page: int
    per_page: int


class ExtractionReviewRequest(BaseModel):
    approved: bool
    comments: Optional[str] = None
