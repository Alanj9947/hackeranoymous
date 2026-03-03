"""Call and CallTranscript models."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Call(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "calls"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True
    )

    # Twilio metadata
    twilio_call_sid: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    direction: Mapped[str] = mapped_column(String(20))  # inbound, outbound
    from_number: Mapped[Optional[str]] = mapped_column(String(20))
    to_number: Mapped[Optional[str]] = mapped_column(String(20))

    # Call state
    status: Mapped[str] = mapped_column(
        String(30), default="initiated", index=True
    )  # initiated, ringing, in-progress, completed, failed, no-answer, busy
    started_at: Mapped[Optional[str]] = mapped_column(String(50))
    ended_at: Mapped[Optional[str]] = mapped_column(String(50))
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)

    # Recording
    recording_url: Mapped[Optional[str]] = mapped_column(String(500))
    recording_s3_key: Mapped[Optional[str]] = mapped_column(String(500))

    # AI processing
    stt_model: Mapped[Optional[str]] = mapped_column(String(50))
    llm_model: Mapped[Optional[str]] = mapped_column(String(50))
    tts_model: Mapped[Optional[str]] = mapped_column(String(50))
    ai_cost_usd: Mapped[Optional[float]] = mapped_column(Float)

    # Metadata
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="calls", lazy="selectin")  # noqa: F821
    transcript: Mapped[Optional["CallTranscript"]] = relationship(
        "CallTranscript", back_populates="call", uselist=False, lazy="selectin"
    )
    extracted_data: Mapped[Optional["ExtractedCallData"]] = relationship(  # noqa: F821
        "ExtractedCallData", back_populates="call", uselist=False, lazy="selectin"
    )


class CallTranscript(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "call_transcripts"

    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calls.id"), unique=True, nullable=False
    )

    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    segments: Mapped[Optional[dict]] = mapped_column(JSONB)
    # Segments: [{speaker, text, start_time, end_time, confidence}, ...]

    language: Mapped[Optional[str]] = mapped_column(String(10))
    word_count: Mapped[Optional[int]] = mapped_column(Integer)

    # Relationship
    call: Mapped["Call"] = relationship("Call", back_populates="transcript")
