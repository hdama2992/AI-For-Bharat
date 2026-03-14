"""Shared orchestration and agent session models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.models.health import ChatMessage


class AgentType(str, Enum):
    SUPERVISOR = "supervisor"
    HEALTH = "health"
    ONBOARDING = "onboarding"
    MANDI = "mandi"
    FALLBACK = "fallback"


class RoutingDecision(BaseModel):
    agent: AgentType
    confidence: float = Field(ge=0.0, le=1.0)
    handoff_reason: str
    continue_current: bool = False
    source: Literal["bedrock", "fallback"] = "fallback"
    model: Optional[str] = None


class SessionSummary(BaseModel):
    text: str = ""
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentSession(BaseModel):
    session_id: str
    household_id: Optional[str] = None
    channel: Literal["web", "whatsapp"] = "web"
    active_agent: AgentType = AgentType.SUPERVISOR
    messages: List[ChatMessage] = []
    routing_history: List[RoutingDecision] = []
    slots: Dict[str, Dict[str, Any]] = {}
    summary: SessionSummary = Field(default_factory=SessionSummary)
    last_triage: Optional[Dict[str, Any]] = None
    whatsapp_from_number: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChatRouteRequest(BaseModel):
    session_id: str
    channel: Literal["web", "whatsapp"] = "web"
    message: str
    household_id: Optional[str] = None
    language: Literal["en", "hi"] = "en"
    force_agent: Optional[AgentType] = None
    whatsapp_from_number: Optional[str] = None


class ChatRouteResponse(BaseModel):
    agent: AgentType
    model: str
    source: Literal["bedrock", "fallback"]
    handoff_reason: str
    reply_text: str
    structured_payload: Optional[Dict[str, Any]] = None
    session_id: str
    routing_confidence: float = Field(ge=0.0, le=1.0)


class StoredMediaReference(BaseModel):
    media_id: str
    storage: Literal["memory", "s3"]
    content_type: str
    key: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

