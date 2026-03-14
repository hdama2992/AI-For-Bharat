"""Health specialist agent wrapper around the shared health advisor."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.config import get_settings
from app.models.health import ChatMessage
from app.services.health_advisor import health_advisor

settings = get_settings()


class HealthAgent:
    def handle_turn(
        self,
        user_message: str,
        conversation_history: List[ChatMessage],
        household_context: Dict[str, Any] | None,
        language: str = "en",
    ) -> Tuple[str, Dict[str, Any]]:
        reply = health_advisor.generate_reply(
            user_message=user_message,
            conversation_history=conversation_history,
            household_context=household_context,
            language=language,
        )
        payload: Dict[str, Any] = {
            "triage": reply.triage.model_dump() if reply.triage else None,
            "slots": health_advisor.extract_structured_signals(user_message, household_context),
            "model": settings.bedrock_model_id if reply.source == "bedrock" else "fallback-health",
            "source": reply.source,
        }
        return reply.display_text, payload


health_agent = HealthAgent()

