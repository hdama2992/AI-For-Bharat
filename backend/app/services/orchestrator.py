"""Shared multi-agent orchestration for web and WhatsApp channels."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.db.repository import repository
from app.models.chat import AgentSession, AgentType, ChatRouteResponse
from app.models.health import ChatMessage
from app.services.agents.health_agent import health_agent
from app.services.agents.mandi_agent import mandi_agent
from app.services.agents.onboarding_agent import onboarding_agent
from app.services.agents.supervisor import supervisor_agent
from app.services.dpi import (
    slot_filling_orchestrator,
    DPIService,
    jan_aushadhi_service,
    transport_service,
    abdm_hfr_service,
)


class Orchestrator:
    def route_turn(
        self,
        session_id: str,
        channel: str,
        message: str,
        household_id: Optional[str] = None,
        language: str = "en",
        force_agent: Optional[AgentType] = None,
        whatsapp_from_number: Optional[str] = None,
    ) -> ChatRouteResponse:
        session = repository.get_agent_session(session_id)
        if not session:
            session = AgentSession(
                session_id=session_id,
                household_id=household_id,
                channel=channel,
                whatsapp_from_number=whatsapp_from_number,
            )
        else:
            if household_id and not session.household_id:
                session.household_id = household_id
            if whatsapp_from_number and not session.whatsapp_from_number:
                session.whatsapp_from_number = whatsapp_from_number

        session.messages.append(ChatMessage(role="user", content=message))

        routing = (
            supervisor_agent.route(message, active_agent=session.active_agent)
            if force_agent is None
            else supervisor_agent._fallback_route(message, force_agent)  # noqa: SLF001 - simple forced route for module pages
        )
        selected_agent = force_agent or routing.agent
        session.active_agent = selected_agent
        session.routing_history.append(routing)

        household_context = self._build_household_context(session.household_id)
        reply_text, specialist = self._dispatch(
            agent=selected_agent,
            session=session,
            message=message,
            household_context=household_context,
            language=language,
        )

        session.messages.append(ChatMessage(role="assistant", content=reply_text))
        session.slots[selected_agent.value] = specialist.get("slots", session.slots.get(selected_agent.value, {}))
        if specialist.get("triage"):
            session.last_triage = specialist["triage"]
        session.summary.text = f"{selected_agent.value}: {reply_text[:180]}"
        repository.upsert_agent_session(session)

        return ChatRouteResponse(
            agent=selected_agent,
            model=specialist.get("model", routing.model or "fallback"),
            source=specialist.get("source", routing.source),
            handoff_reason=routing.handoff_reason,
            reply_text=reply_text,
            structured_payload=specialist.get("structured_payload") or ({"triage": specialist.get("triage")} if specialist.get("triage") else None),
            session_id=session.session_id,
            routing_confidence=routing.confidence,
        )

    def get_session(self, session_id: str) -> Optional[AgentSession]:
        return repository.get_agent_session(session_id)

    def list_sessions(self, household_id: Optional[str] = None, limit: int = 20) -> List[AgentSession]:
        return repository.list_agent_sessions(household_id=household_id, limit=limit)

    def _build_household_context(self, household_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not household_id:
            return None
        household = repository.get_household(household_id)
        if not household:
            return None
        return {
            "name": household.name,
            "district": household.district,
            "state": household.state,
            "crop_primary": household.crop_primary,
            "family_members": [member.model_dump() for member in household.family_members],
        }

    def _dispatch(
        self,
        agent: AgentType,
        session: AgentSession,
        message: str,
        household_context: Optional[Dict[str, Any]],
        language: str,
    ) -> tuple[str, Dict[str, Any]]:
        if agent == AgentType.HEALTH:
            history = session.messages[:-1]
            return health_agent.handle_turn(
                user_message=message,
                conversation_history=history,
                household_context=household_context,
                language=language,
            )
        if agent == AgentType.ONBOARDING:
            return onboarding_agent.handle_turn(session, message)
        if agent == AgentType.MANDI:
            return mandi_agent.handle_turn(session, message, language=language)

        # Use DPI slot-filling orchestrator for fallback cases
        # This handles Jan Aushadhi, Transport, and enhanced intent detection
        return self._handle_dpi_query(session, message, household_context, language)

    def _handle_dpi_query(
        self,
        session: AgentSession,
        message: str,
        household_context: Optional[Dict[str, Any]],
        language: str,
    ) -> tuple[str, Dict[str, Any]]:
        """
        Handle DPI queries using Evidence-First Slot-Filling.
        Routes to Jan Aushadhi, Transport, or provides helpful fallback.
        """
        # Get current DPI slots from session
        dpi_slots = session.slots.get("dpi", {})

        # Process through slot-filling orchestrator
        result = slot_filling_orchestrator.process_turn(
            user_message=message,
            current_slots=dpi_slots,
            household_context=household_context,
            language=language[:2] if language else "en",  # "en" or "hi"
        )

        service = result.get("service")

        # If slots incomplete, ask clarifying question
        if not result.get("ready_for_api"):
            if result.get("clarifying_question"):
                return result["clarifying_question"], {
                    "slots": result.get("slots", {}),
                    "model": "bedrock-haiku",
                    "source": "dpi_orchestrator",
                }
            # No specific DPI service detected
            reply = (
                "I can help with health, mandi prices, generic medicines (Jan Aushadhi), "
                "or transport costs. What would you like to know?\n\n"
                "मैं स्वास्थ्य, मंडी भाव, जेनेरिक दवाइयाँ (जन औषधि), "
                "या ट्रांसपोर्ट खर्च में मदद कर सकता हूँ। आप क्या जानना चाहते हैं?"
            )
            return reply, {"slots": {}, "model": "fallback", "source": "fallback"}

        # All slots filled - call the appropriate DPI service
        api_params = result.get("api_params", {})

        if service == DPIService.JAN_AUSHADHI:
            jak_result = jan_aushadhi_service.search_kendras(
                district=api_params.get("district", "Harda"),
                state=api_params.get("state", "Madhya Pradesh"),
            )
            reply_key = "response_text_hi" if language.startswith("hi") else "response_text_en"
            return jak_result.get(reply_key, jak_result.get("message", "No results found")), {
                "slots": result.get("slots", {}),
                "structured_payload": jak_result,
                "model": "bedrock-haiku",
                "source": "jan_aushadhi_mock",
            }

        if service == DPIService.TRANSPORT:
            transport_result = transport_service.estimate_transport(
                from_location=api_params.get("from_location", "Harda"),
                to_mandi=api_params.get("to_mandi"),
                quantity_quintals=float(api_params.get("quantity_quintals", 10)),
            )
            reply_key = "response_text_hi" if language.startswith("hi") else "response_text_en"
            return transport_result.get(reply_key, "Transport estimate not available"), {
                "slots": result.get("slots", {}),
                "structured_payload": transport_result,
                "model": "bedrock-haiku",
                "source": "transport_mock",
            }

        if service == DPIService.HEALTH_FACILITY:
            hfr_result = abdm_hfr_service.search_facilities(
                district=api_params.get("district", "Harda"),
                state=api_params.get("state", "Madhya Pradesh"),
                facility_type=api_params.get("facility_type"),
                specialty=api_params.get("specialty"),
            )
            reply_key = "response_text_hi" if language.startswith("hi") else "response_text_en"
            return hfr_result.get(reply_key, hfr_result.get("message", "No facilities found")), {
                "slots": result.get("slots", {}),
                "structured_payload": hfr_result,
                "model": "bedrock-haiku",
                "source": "abdm_hfr_mock",
            }

        # Default fallback
        reply = (
            "I can help with health, mandi prices, generic medicines (Jan Aushadhi), "
            "or transport costs. What would you like to know?\n\n"
            "मैं स्वास्थ्य, मंडी भाव, जेनेरिक दवाइयाँ (जन औषधि), "
            "या ट्रांसपोर्ट खर्च में मदद कर सकता हूँ। आप क्या जानना चाहते हैं?"
        )
        return reply, {"slots": {}, "model": "fallback", "source": "fallback"}


orchestrator = Orchestrator()

