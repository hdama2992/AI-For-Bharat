"""Onboarding specialist agent."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.config import get_settings
from app.models.chat import AgentSession
from app.models.household import OnboardTurn
from app.services.onboarding import onboarding_service

settings = get_settings()


class OnboardingAgent:
    REQUIRED_FIELDS = ["name", "state", "district", "crop_primary", "land_acres"]

    def handle_turn(self, session: AgentSession, user_message: str) -> Tuple[str, Dict[str, Any]]:
        turns = [
            OnboardTurn(question=entry.get("question", "User provided household details"), answer=entry.get("answer", ""))
            for entry in session.slots.get("onboarding", {}).get("turns", [])
        ]
        turns.append(OnboardTurn(question="Latest onboarding turn", answer=user_message))
        extracted = onboarding_service.extract(turns, prefill={})

        household = extracted.get("household", {})
        missing = extracted.get("missing_fields", [])
        slots = {
            "turns": [{"question": turn.question, "answer": turn.answer} for turn in turns],
            "household": household,
            "missing_fields": missing,
            "confidence": extracted.get("confidence", 0.5),
        }

        if missing:
            next_field = missing[0]
            prompt = self._next_question(next_field)
            reply = (
                f"I have captured some profile details. {prompt}\n\n"
                f"मैंने कुछ जानकारी समझ ली है। {self._next_question_hi(next_field)}"
            )
        else:
            reply = (
                "Your household profile is ready for confirmation. Please review the extracted details below and confirm.\n\n"
                "आपकी प्रोफ़ाइल लगभग तैयार है। कृपया नीचे दी गई जानकारी देखकर पुष्टि करें।"
            )

        return reply, {
            "household": household,
            "missing_fields": missing,
            "confidence": extracted.get("confidence", 0.5),
            "slots": slots,
            "model": settings.onboarding_model_id if extracted.get("confidence", 0) >= 0.5 else "fallback-onboarding",
            "source": "bedrock" if extracted.get("confidence", 0) >= 0.5 else "fallback",
        }

    def _next_question(self, field: str) -> str:
        prompts = {
            "name": "What is the household head's name?",
            "state": "Which state do you live in?",
            "district": "Which district do you live in?",
            "crop_primary": "What is your main crop?",
            "land_acres": "How much land do you have in acres?",
        }
        return prompts.get(field, "Please share the missing household detail.")

    def _next_question_hi(self, field: str) -> str:
        prompts = {
            "name": "घर के मुखिया का नाम बताइए।",
            "state": "आप किस राज्य में रहते हैं?",
            "district": "आप किस जिले में रहते हैं?",
            "crop_primary": "आपकी मुख्य फसल कौन सी है?",
            "land_acres": "आपके पास कितनी जमीन है, एकड़ में?",
        }
        return prompts.get(field, "कृपया बाकी जानकारी बताइए।")


onboarding_agent = OnboardingAgent()

