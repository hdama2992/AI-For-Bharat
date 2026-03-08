"""Shared multi-agent orchestration routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.orchestrator import orchestrator
from app.models.chat import ChatRouteRequest, ChatRouteResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/route", response_model=ChatRouteResponse)
async def route_chat_turn(request: ChatRouteRequest):
    """Route a generic user turn through the supervisor and specialists."""
    return orchestrator.route_turn(
        session_id=request.session_id,
        channel=request.channel,
        message=request.message,
        household_id=request.household_id,
        language=request.language,
        force_agent=request.force_agent,
        whatsapp_from_number=request.whatsapp_from_number,
    )


@router.get("/session/{session_id}")
async def get_chat_session(session_id: str):
    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/sessions")
async def list_chat_sessions(household_id: str | None = None, limit: int = 10):
    return {"sessions": orchestrator.list_sessions(household_id=household_id, limit=limit)}

