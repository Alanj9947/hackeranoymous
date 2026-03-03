"""Scheduled exports and export history models."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Time
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ScheduledExport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "scheduled_exports"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Schedule
    frequency: Mapped[str] = mapped_column(String(50))  # daily, weekly, monthly
    scheduled_time: Mapped[Optional[str]] = mapped_column(String(10))  # HH:MM
    days_of_week: Mapped[Optional[list]] = mapped_column(ARRAY(Integer))
    day_of_month: Mapped[Optional[int]] = mapped_column(Integer)

    # Export settings
    destination: Mapped[str] = mapped_column(String(50))  # excel, sheets, csv
    destination_config: Mapped[Optional[dict]] = mapped_column(JSONB)
    template_name: Mapped[Optional[str]] = mapped_column(String(255))
    columns_to_export: Mapped[Optional[list]] = mapped_column(ARRAY(String))

    # Filters
    filters: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Status
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[Optional[str]] = mapped_column(String(50))
    next_run_at: Mapped[Optional[str]] = mapped_column(String(50))
    last_run_status: Mapped[Optional[str]] = mapped_column(String(50))
    last_run_error: Mapped[Optional[str]] = mapped_column(Text)
    run_count: Mapped[int] = mapped_column(Integer, default=0)


class ExportHistory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "export_history"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    scheduled_export_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheduled_exports.id")
    )

    export_type: Mapped[str] = mapped_column(String(50))  # manual, scheduled, api
    destination: Mapped[str] = mapped_column(String(50))  # excel, sheets, csv, webhook
    call_ids: Mapped[Optional[list]] = mapped_column(ARRAY(UUID(as_uuid=True)))

    rows_exported: Mapped[Optional[int]] = mapped_column(Integer)
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(String(50), default="processing")
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    completed_at: Mapped[Optional[str]] = mapped_column(String(50))
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
