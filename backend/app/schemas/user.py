"""User management schemas."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    avatar_url: Optional[str] = None
    role: Optional[str] = None  # only admin/owner can change


class UserListResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class CompanyResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    plan: str
    is_active: bool

    model_config = {"from_attributes": True}
