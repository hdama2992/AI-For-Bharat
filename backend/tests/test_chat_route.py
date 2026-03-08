from app.models.chat import AgentType
from app.services.bedrock import bedrock_service
from app.services.orchestrator import orchestrator


def test_route_chat_turn_returns_mandi_payload(monkeypatch):
    monkeypatch.setattr(bedrock_service, "is_configured", lambda: False)
    response = orchestrator.route_turn(
        session_id="test-mandi-session",
        channel="web",
        message="What is the soybean price in Harda mandi today?",
        language="en",
    )

    assert response.agent == AgentType.MANDI
    assert response.structured_payload is not None


def test_route_chat_turn_returns_health_reply(monkeypatch):
    monkeypatch.setattr(bedrock_service, "is_configured", lambda: False)
    response = orchestrator.route_turn(
        session_id="test-health-session",
        channel="web",
        message="My 8 year old daughter has 103 F fever and vomiting since morning",
        language="hi",
    )

    assert response.agent == AgentType.HEALTH
    assert response.reply_text
