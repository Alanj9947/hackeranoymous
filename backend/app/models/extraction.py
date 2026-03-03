"""Extracted call data and extraction job queue models."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ExtractedCallData(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "extracted_call_data"

    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calls.id"), unique=True, nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )

    # Extraction metadata
    extraction_method: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # custom_server, openai, manual
    model_used: Mapped[Optional[str]] = mapped_column(String(255))
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)

    # Main extracted data (flexible JSONB)
    extracted_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Keys: customer{name,email,phone,company,accountId}, issue{category,severity,description,tags},
    #   resolution{provided,status,nextSteps}, sentiment{overall,score,emotionalCues},
    #   actionItems[{action,owner,dueDate,priority}], keyMetrics{...}, customFields{}

    # Quality control
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    approved: Mapped[Optional[bool]] = mapped_column(Boolean)
    quality_comments: Mapped[Optional[str]] = mapped_column(Text)

    # Export tracking
    exported: Mapped[bool] = mapped_column(Boolean, default=False)
    export_destinations: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Relationships
    call: Mapped["Call"] = relationship("Call", back_populates="extracted_data")  # noqa: F821


class DataExtractionJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "data_extraction_jobs"

    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calls.id"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50), default="queued", index=True
    )  # queued, processing, completed, failed
    priority: Mapped[int] = mapped_column(Integer, default=1)

    started_at: Mapped[Optional[str]] = mapped_column(String(50))
    completed_at: Mapped[Optional[str]] = mapped_column(String(50))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)

    result_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("extracted_call_data.id")
    )
