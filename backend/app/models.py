"""Pydantic models for the API."""
from typing import Literal

from pydantic import BaseModel, Field


Role = Literal["system", "user", "assistant"]


class Message(BaseModel):
    role: Role
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(..., min_length=1)
    model: str | None = Field(default=None, description="Model name. If null, OmniRoute chooses.")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=8192)


class ChatResponse(BaseModel):
    content: str
    model: str | None = None
    usage: dict | None = None
    combo: str | None = Field(default=None, description="Combo ID used (echoed back)")


class HealthResponse(BaseModel):
    status: str
    service: str
    omni_configured: bool
