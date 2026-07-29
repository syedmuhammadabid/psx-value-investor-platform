"""Authentication request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

_PW_MIN = 8
_PW_MAX = 128


class UserCreate(BaseModel):
    """Registration payload."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=_PW_MIN, max_length=_PW_MAX)
    full_name: str | None = Field(default=None, max_length=200)


class UserLogin(BaseModel):
    """Login payload."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=_PW_MAX)


class UserOut(BaseModel):
    """Public user representation (never exposes the password hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None
    created_at: datetime


class Token(BaseModel):
    """A freshly issued access token."""

    access_token: str
    token_type: str = "bearer"
