from app.models.chat import AgentType
from app.services.bedrock import bedrock_service
from app.services.agents.supervisor import supervisor_agent


def test_supervisor_routes_health_symptoms(monkeypatch):
    monkeypatch.setattr(bedrock_service, "is_configured", lambda: False)
    decision = supervisor_agent.route("My child has fever and vomiting")
    assert decision.agent == AgentType.HEALTH


def test_supervisor_routes_mandi_question(monkeypatch):
    monkeypatch.setattr(bedrock_service, "is_configured", lambda: False)
    decision = supervisor_agent.route("What is the soybean price in Harda mandi today?")
    assert decision.agent == AgentType.MANDI


def test_supervisor_routes_onboarding_details(monkeypatch):
    monkeypatch.setattr(bedrock_service, "is_configured", lambda: False)
    decision = supervisor_agent.route("My name is Rajesh and I farm 5 acres in Harda")
    assert decision.agent == AgentType.ONBOARDING
