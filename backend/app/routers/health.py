"""
Health Triage Router
- Streaming chat with Sehat Agent
- SSE (Server-Sent Events) for real-time responses
"""
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import Generator

from app.models.health import HealthChatRequest, ChatMessage
from app.services.health_advisor import health_advisor
from app.db.memory import get_household

router = APIRouter(prefix="/health", tags=["Health"])


def generate_sse_stream(
    user_message: str,
    conversation_history: list,
    household_context: dict,
    language: str,
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

    if reply.triage:
        triage_data = {
            "triage": {
                "triage_level": reply.triage.triage_level.value,
                "confidence_pct": reply.triage.confidence_pct,
                "assessment_summary": reply.triage.assessment_summary,
                "immediate_actions": reply.triage.immediate_actions,
                "follow_up": reply.triage.follow_up,
                "emergency_number": reply.triage.emergency_number,
                "disclaimer": reply.triage.disclaimer,
            }
        }
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
        household = get_household(request.household_id)
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
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
