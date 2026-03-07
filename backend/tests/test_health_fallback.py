from app.models.health import ChatMessage, TriageLevel
from app.services.health_advisor import health_advisor


def test_health_fallback_red_triage_for_child_high_fever():
    reply = health_advisor.generate_reply(
        user_message="My 8 year old daughter has 103 F fever and vomiting since morning",
        conversation_history=[],
        household_context=None,
        language="hi",
    )

    assert reply.triage is not None
    assert reply.triage.triage_level == TriageLevel.RED


def test_health_fallback_green_triage_for_mild_headache():
    reply = health_advisor.generate_reply(
        user_message="I have mild headache since today",
        conversation_history=[],
        household_context=None,
        language="en",
    )

    assert reply.triage is not None
    assert reply.triage.triage_level == TriageLevel.GREEN


def test_health_fallback_clarifies_when_context_is_missing():
    reply = health_advisor.generate_reply(
        user_message="Fever",
        conversation_history=[],
        household_context=None,
        language="en",
    )

    assert reply.triage is None
    assert "who is sick" in reply.display_text.lower()
