"""Custom AI server schemas."""

from __future__ import annotations

from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CustomServerConfigCreate(BaseModel):
    endpoint: str = Field(..., min_length=5)
    api_key: str = Field(..., min_length=8)
    model_name: Optional[str] = None
    timeout_seconds: int = Field(120, ge=10, le=600)
    max_retries: int = Field(2, ge=0, le=5)
    enabled: bool = True
    fallback_to_openai: bool = True
    agent_id: Optional[UUID] = None


class CustomServerConfigResponse(BaseModel):
    id: UUID
    company_id: UUID
    agent_id: Optional[UUID] = None
    endpoint: str
    model_name: Optional[str] = None
    timeout_seconds: int
    max_retries: int
    enabled: bool
    health_status: Optional[str] = None
    last_health_check: Optional[str] = None
    last_response_time_ms: Optional[int] = None
    fallback_to_openai: bool

    model_config = {"from_attributes": True}


class CustomServerHealthResponse(BaseModel):
    status: str
    endpoint: str
    last_check: Optional[str] = None
    response_time: Optional[int] = None  # ms
    model_loaded: Optional[str] = None
    models_available: Optional[List[str]] = None
    gpu_available: Optional[bool] = None
    gpu_memory_usage: Optional[str] = None
    request_queue_depth: Optional[int] = None
    uptime: Optional[str] = None
