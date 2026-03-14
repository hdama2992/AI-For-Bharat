"""
Health Triage Router
- Streaming chat with Sehat Agent
- SSE (Server-Sent Events) for real-time responses
"""
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import Generator

from app.db.repository import repository
from app.models.chat import AgentSession, AgentType, RoutingDecision, SessionSummary
from app.models.health import HealthChatRequest, ChatMessage
from app.services.health_advisor import health_advisor

router = APIRouter(prefix="/health", tags=["Health"])


def generate_sse_stream(
    user_message: str,
    conversation_history: list,
    household_context: dict,
    language: str,
    session_id: str,
    household_id: str,
) -> Generator[str, None, None]:
    """Generate SSE stream for health chat"""
    history = [
        ChatMessage(role=msg.get("role", "user"), content=msg.get("content", ""))
        for msg in conversation_history
        if msg.get("content")
    ]

    reply = yield from _stream_health_reply(
        user_message=user_message,
        conversation_history=history,
        household_context=household_context,
        language=language,
    )

    structured_payload = {
        "agent": "health",
        "model": "fallback-health",
        "source": reply.source,
        "handoff_reason": "Health module invoked directly.",
        "session_id": session_id,
        "routing_confidence": 1.0,
    }
    if reply.source == "bedrock":
        structured_payload["model"] = "bedrock-health"
    yield f"event: route\ndata: {json.dumps(structured_payload)}\n\n"

    existing = repository.get_agent_session(session_id)
    session = existing or AgentSession(
        session_id=session_id,
        household_id=household_id,
        channel="web",
        active_agent=AgentType.HEALTH,
    )
    session.active_agent = AgentType.HEALTH
    session.messages.extend([
        ChatMessage(role="user", content=user_message),
        ChatMessage(role="assistant", content=reply.display_text),
    ])
    session.routing_history.append(
        RoutingDecision(
            agent=AgentType.HEALTH,
            confidence=1.0,
            handoff_reason="Health module invoked directly.",
            continue_current=existing is not None and existing.active_agent == AgentType.HEALTH,
            source=reply.source,
            model=structured_payload["model"],
        )
    )
    session.slots["health"] = health_advisor.extract_structured_signals(user_message, household_context)
    session.last_triage = reply.triage.model_dump() if reply.triage else None
    session.summary = SessionSummary(text=f"health: {reply.display_text[:180]}")
    repository.upsert_agent_session(session)

    if reply.triage:
        triage_data = {"triage": reply.triage.model_dump()}
        yield f"event: triage\ndata: {json.dumps(triage_data)}\n\n"

    yield "data: [DONE]\n\n"


def _stream_health_reply(
    user_message: str,
    conversation_history: list[ChatMessage],
    household_context: dict,
    language: str,
):
    generator = health_advisor.stream_reply(
        user_message=user_message,
        conversation_history=conversation_history,
        household_context=household_context,
        language=language,
    )
    try:
        while True:
            chunk = next(generator)
            yield f"data: {chunk}\n\n"
    except StopIteration as stop:
        return stop.value


@router.post("/chat")
async def health_chat(request: HealthChatRequest):
    """
    Streaming health chat endpoint.
    Returns SSE stream with:
    - data: <text chunk> for assistant response
    - event: triage + data: {triage JSON} when triage is ready
    - data: [DONE] when complete
    """
    
    # Get household context if available
    household_context = {}
    if request.household_id:
        household = repository.get_household(request.household_id)
        if household:
            household_context = {
                "name": household.name,
                "district": household.district,
                "family_members": [
                    {
                        "name": m.name,
                        "age": m.age,
                        "relation": m.relation,
                        "gender": m.gender,
                        "is_pregnant": m.is_pregnant,
                        "chronic_conditions": m.chronic_conditions,
                    }
                    for m in household.family_members
                ],
            }
    
    # Convert Pydantic models to dicts for history
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in request.conversation_history
    ]
    
    return StreamingResponse(
        generate_sse_stream(
            user_message=request.message,
            conversation_history=history,
            household_context=household_context,
            language=request.language,
            session_id=request.session_id or "health-web-session",
            household_id=request.household_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
