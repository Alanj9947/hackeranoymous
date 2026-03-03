"""Call-related schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CallCreate(BaseModel):
    agent_id: UUID
    direction: str = "outbound"
    to_number: str = Field(..., min_length=10)
    metadata_json: Optional[Dict[str, Any]] = None


class CallResponse(BaseModel):
    id: UUID
    company_id: UUID
    agent_id: UUID
    twilio_call_sid: Optional[str] = None
    direction: str
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    status: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    duration_seconds: Optional[int] = None
    recording_url: Optional[str] = None
    stt_model: Optional[str] = None
    llm_model: Optional[str] = None
    tts_model: Optional[str] = None
    ai_cost_usd: Optional[float] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: Any = None

    model_config = {"from_attributes": True}


class CallListResponse(BaseModel):
    calls: List[CallResponse]
    total: int
    page: int
    per_page: int


class TranscriptResponse(BaseModel):
    id: UUID
    call_id: UUID
    full_text: str
    segments: Optional[List[Dict[str, Any]]] = None
    language: Optional[str] = None
    word_count: Optional[int] = None

    model_config = {"from_attributes": True}
