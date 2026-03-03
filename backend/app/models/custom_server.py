"""Custom AI server configuration model."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class CustomServerConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "custom_server_configs"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )

    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(String(500))
    model_name: Mapped[Optional[str]] = mapped_column(String(255))

    timeout_seconds: Mapped[int] = mapped_column(Integer, default=120)
    max_retries: Mapped[int] = mapped_column(Integer, default=2)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    health_check_interval: Mapped[int] = mapped_column(Integer, default=30)
    health_status: Mapped[Optional[str]] = mapped_column(String(50))  # healthy, unhealthy, unknown
    last_health_check: Mapped[Optional[str]] = mapped_column(String(50))
    last_response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)

    fallback_to_openai: Mapped[bool] = mapped_column(Boolean, default=True)
