"""Phone number model for Twilio-provisioned numbers."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PhoneNumber(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Twilio-provisioned phone numbers assigned to agents."""

    __tablename__ = "phone_numbers"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id"), index=True
    )

    # Phone number details
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    twilio_phone_sid: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    friendly_name: Mapped[Optional[str]] = mapped_column(String(100))

    # Phone number metadata
    country_code: Mapped[str] = mapped_column(String(2), default="US")
    area_code: Mapped[Optional[str]] = mapped_column(String(10))
    locality: Mapped[Optional[str]] = mapped_column(String(100))
    region: Mapped[Optional[str]] = mapped_column(String(100))
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))

    # Status and capabilities
    status: Mapped[str] = mapped_column(
        String(20), default="active"
    )  # active, inactive, provisioning, failed
    monthly_cost: Mapped[float] = mapped_column(Float, default=1.00)
    inbound_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    outbound_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Webhook configuration
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500))
    webhook_configured_at: Mapped[Optional[str]] = mapped_column(String(50))

    # Timestamps for provisioning lifecycle
    provisioned_at: Mapped[Optional[str]] = mapped_column(String(50))
    released_at: Mapped[Optional[str]] = mapped_column(String(50))

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(String(500))

    # Metadata
    call_count: Mapped[int] = mapped_column(default=0)
    last_call_at: Mapped[Optional[str]] = mapped_column(String(50))

    # Relationships
    agent: Mapped[Optional["Agent"]] = relationship(
        "Agent", lazy="selectin"
    )  # noqa: F821
