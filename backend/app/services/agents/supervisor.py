"""Supervisor agent for Python-orchestrated Bedrock multi-agent routing."""

from __future__ import annotations

import json
from typing import Optional

from app.config import get_settings
from app.models.chat import AgentType, RoutingDecision
from app.services.agents.prompts import SUPERVISOR_AGENT_PROMPT
from app.services.bedrock import bedrock_service

settings = get_settings()


class SupervisorAgent:
    def route(self, message: str, active_agent: Optional[AgentType] = None) -> RoutingDecision:
        if bedrock_service.is_configured():
            try:
                prompt = (
                    f"Current active agent: {active_agent.value if active_agent else 'none'}\n"
                    f"Latest user message: {message}"
                )
                response = bedrock_service.invoke(
                    [{"role": "user", "content": prompt}],
                    system_prompt=SUPERVISOR_AGENT_PROMPT,
                    model_id=settings.supervisor_model_id,
                    max_tokens=300,
                    temperature=settings.bedrock_router_temperature,
                ).strip()
                cleaned = response.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.strip("`")
                    cleaned = cleaned.replace("json", "", 1).strip()
                parsed = json.loads(cleaned)
                return RoutingDecision(
                    agent=AgentType(parsed.get("agent", "fallback")),
                    confidence=float(parsed.get("confidence", 0.7)),
                    handoff_reason=parsed.get("handoff_reason", "Supervisor selected this agent."),
                    continue_current=bool(parsed.get("continue_current", False)),
                    source="bedrock",
                    model=settings.supervisor_model_id,
                )
            except Exception as exc:
                print(f"Supervisor fallback triggered: {exc}")

        return self._fallback_route(message, active_agent)

    def _fallback_route(self, message: str, active_agent: Optional[AgentType]) -> RoutingDecision:
        lowered = message.lower()
        if any(word in lowered for word in ["fever", "pain", "vomit", "cough", "bukh", "बुखार", "उल्टी", "दर्द"]):
            agent = AgentType.HEALTH
            reason = "Health symptoms detected."
        elif any(word in lowered for word in ["mandi", "price", "sell", "soybean", "wheat", "crop price", "भाव"]):
            agent = AgentType.MANDI
            reason = "Market price question detected."
        elif any(word in lowered for word in ["name", "district", "family", "land", "profile", "crop", "गांव", "परिवार"]):
            agent = AgentType.ONBOARDING
            reason = "Profile or household details detected."
        else:
            agent = active_agent or AgentType.FALLBACK
            reason = "No clear specialist intent found."

        return RoutingDecision(
            agent=agent,
            confidence=0.66 if agent != AgentType.FALLBACK else 0.35,
            handoff_reason=reason,
            continue_current=active_agent == agent,
            source="fallback",
            model="fallback-router",
        )


supervisor_agent = SupervisorAgent()

