"""Agent configuration schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SystemPromptConfig(BaseModel):
    personality: str = ""
    goals: List[str] = []
    environment: str = ""
    constraints: List[str] = []
    firstMessage: str = ""
    tone: str = "professional"
    language: str = "en"


class VoiceSettingsConfig(BaseModel):
    provider: str = "elevenlabs"  # elevenlabs, azure, openai
    voiceId: str = ""
    speed: float = Field(1.0, ge=0.5, le=2.0)
    pitch: float = 0.0


class CallSettingsConfig(BaseModel):
    maxDurationSeconds: int = 600
    enableRecording: bool = True
    recordingWebhook: Optional[str] = None
    timeout: int = 30
    transferNumber: Optional[str] = None


class DataExtractionConfig(BaseModel):
    enabled: bool = False
    extractionPrompt: str = ""
    customServer: Optional[Dict[str, Any]] = None
    fallbackToOpenAI: bool = True
    fieldsToExtract: Dict[str, str] = {}


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: Optional[SystemPromptConfig] = None
    voice_settings: Optional[VoiceSettingsConfig] = None
    call_settings: Optional[CallSettingsConfig] = None
    data_extraction: Optional[DataExtractionConfig] = None
    phone_numbers: Optional[List[str]] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    system_prompt: Optional[SystemPromptConfig] = None
    voice_settings: Optional[VoiceSettingsConfig] = None
    call_settings: Optional[CallSettingsConfig] = None
    data_extraction: Optional[DataExtractionConfig] = None
    phone_numbers: Optional[List[str]] = None


class AgentResponse(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    description: Optional[str] = None
    status: str
    system_prompt: Dict[str, Any] = {}
    voice_settings: Dict[str, Any] = {}
    call_settings: Dict[str, Any] = {}
    data_extraction: Dict[str, Any] = {}
    phone_numbers: Optional[List[str]] = None
    total_calls: int = 0
    total_minutes: float = 0
    created_at: Any = None
    updated_at: Any = None

    model_config = {"from_attributes": True}


class AgentListResponse(BaseModel):
    agents: List[AgentResponse]
    total: int
    page: int
    per_page: int
