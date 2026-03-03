"""Conversation model for browser-based voice interactions."""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Conversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Browser-based conversation with an agent."""

    __tablename__ = "conversations"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )

    # Conversation metadata
    channel: Mapped[str] = mapped_column(String(20), default="browser")  # browser, phone
    status: Mapped[str] = mapped_column(
        String(30), default="active"
    )  # active, completed, failed
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)

    # Timestamps
    started_at: Mapped[Optional[str]] = mapped_column(String(50))
    ended_at: Mapped[Optional[str]] = mapped_column(String(50))

    # Content
    transcript: Mapped[Optional[str]] = mapped_column(Text)
    word_count: Mapped[Optional[int]] = mapped_column(Integer)
    sentiment: Mapped[Optional[str]] = mapped_column(String(20))  # positive, neutral, negative

    # AI Processing
    stt_model: Mapped[Optional[str]] = mapped_column(String(50))
    llm_model: Mapped[Optional[str]] = mapped_column(String(50))
    tts_model: Mapped[Optional[str]] = mapped_column(String(50))
    ai_cost_usd: Mapped[Optional[float]] = mapped_column(Float)

    # Recording
    recording_url: Mapped[Optional[str]] = mapped_column(String(500))
    recording_s3_key: Mapped[Optional[str]] = mapped_column(String(500))
    enable_recording: Mapped[bool] = mapped_column(Boolean, default=True)

    # Extracted Data
    extracted_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    extraction_status: Mapped[Optional[str]] = mapped_column(
        String(20), default="pending"
    )  # pending, processing, completed, failed

    # Metadata
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    agent: Mapped["Agent"] = relationship(
        "Agent", lazy="selectin"
    )  # noqa: F821
    messages: Mapped[List["ConversationMessage"]] = relationship(
        "ConversationMessage", back_populates="conversation", cascade="all, delete-orphan"
    )


class ConversationMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Individual messages in a conversation."""

    __tablename__ = "conversation_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True
    )
    speaker: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # user, agent
    message: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[Optional[str]] = mapped_column(String(50))

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )
