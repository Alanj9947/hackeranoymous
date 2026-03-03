"""Agent model – voice agent configuration."""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Agent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "agents"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="inactive")  # active, inactive

    # Voice & Conversation config stored as JSONB for flexibility
    system_prompt: Mapped[dict] = mapped_column(JSONB, default=dict)
    # Expected keys: personality, goals[], environment, constraints[], firstMessage, tone, language

    voice_settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    # Expected keys: provider, voiceId, speed, pitch

    call_settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    # Expected keys: maxDurationSeconds, enableRecording, recordingWebhook, timeout, transferNumber

    # Data extraction config
    data_extraction: Mapped[dict] = mapped_column(JSONB, default=dict)
    # Expected keys: enabled, extractionPrompt, customServer{enabled,endpoint,apiKey,timeout},
    #   fallbackToOpenAI, fieldsToExtract{...}

    phone_numbers: Mapped[Optional[list]] = mapped_column(ARRAY(String), default=list)

    # Stats (denormalized for dashboard speed)
    total_calls: Mapped[int] = mapped_column(Integer, default=0)
    total_minutes: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    # Relationships
    calls: Mapped[List["Call"]] = relationship(  # noqa: F821
        "Call", back_populates="agent", lazy="selectin"
    )
