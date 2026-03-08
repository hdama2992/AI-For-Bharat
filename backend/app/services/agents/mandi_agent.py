"""Mandi specialist agent."""

from __future__ import annotations

from typing import Any, Dict, Tuple

from app.config import get_settings
from app.models.chat import AgentSession
from app.services.mandi_service import compare_mandi_prices_data, mandi_service

settings = get_settings()


class MandiAgent:
    def handle_turn(self, session: AgentSession, user_message: str, language: str = "en") -> Tuple[str, Dict[str, Any]]:
        extracted = mandi_service.extract_query(user_message)
        slots = session.slots.get("mandi", {})
        crop = extracted.get("crop") or slots.get("crop")
        district = extracted.get("district") or slots.get("district")
        quantity = extracted.get("quantity_quintal") or slots.get("quantity_quintal")

        new_slots = {
            "crop": crop,
            "district": district,
            "quantity_quintal": quantity,
            "confidence": extracted.get("confidence", 0.4),
        }

        if not crop or not district:
            reply = (
                "Please tell me the crop and district so I can compare mandi prices.\n\n"
                "कृपया फसल और जिला बताइए ताकि मैं मंडी भाव की तुलना कर सकूं।"
            )
            return reply, {
                "slots": new_slots,
                "structured_payload": {"missing_fields": [field for field, value in {"crop": crop, "district": district}.items() if not value]},
                "model": settings.mandi_model_id,
                "source": "bedrock" if extracted.get("confidence", 0) >= 0.5 else "fallback",
            }

        result = compare_mandi_prices_data(crop=crop, district=district)
        reply = mandi_service.explain_result(result, language=language)
        return reply, {
            "slots": new_slots,
            "structured_payload": result,
            "model": settings.mandi_model_id,
            "source": "bedrock" if extracted.get("confidence", 0) >= 0.5 else "fallback",
        }


mandi_agent = MandiAgent()

