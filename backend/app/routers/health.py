"""
Health Triage Router
- Streaming chat with Sehat Agent
- SSE (Server-Sent Events) for real-time responses
"""
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Generator

from app.models.health import HealthChatRequest, ChatMessage
from app.services.agents.sehat import sehat_agent
from app.db.memory import get_household

router = APIRouter(prefix="/health", tags=["Health"])


def generate_sse_stream(
    user_message: str,
    conversation_history: list,
    household_context: dict,
    language: str,
) -> Generator[str, None, None]:
    """Generate SSE stream for health chat"""
    
    # Convert history to ChatMessage objects
    history = [
        ChatMessage(role=msg.get("role", "user"), content=msg.get("content", ""))
        for msg in conversation_history
        if msg.get("content")
    ]
    
    # Accumulate full response to extract triage
    full_response = ""
    
    # Stream response chunks
    for chunk in sehat_agent.chat_stream(
        user_message=user_message,
        conversation_history=history,
        household_context=household_context,
        language=language,
    ):
        full_response += chunk
        # Send chunk as SSE data event
        yield f"data: {chunk}\n\n"
    
    # Check if triage was generated
    triage = sehat_agent.extract_triage(full_response)
    
    if triage:
        # Send triage as special event
        triage_data = {
            "triage": {
                "triage_level": triage.triage_level.value,
                "confidence_pct": triage.confidence_pct,
                "assessment_summary": triage.assessment_summary,
                "immediate_actions": triage.immediate_actions,
                "follow_up": triage.follow_up,
                "emergency_number": triage.emergency_number,
                "disclaimer": triage.disclaimer,
            }
        }
        yield f"event: triage\ndata: {json.dumps(triage_data)}\n\n"
    
    # Signal end of stream
    yield "data: [DONE]\n\n"


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

