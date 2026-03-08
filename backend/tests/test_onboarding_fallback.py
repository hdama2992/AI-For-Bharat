from app.models.household import OnboardTurn
from app.services.bedrock import bedrock_service
from app.services.onboarding import onboarding_service


def test_onboarding_fallback_uses_prefill_and_family_answer(monkeypatch):
    monkeypatch.setattr(bedrock_service, "is_configured", lambda: False)
    turns = [
        OnboardTurn(question="PM-KISAN record says your name is Ramesh Yadav — is this correct?", answer="yes"),
        OnboardTurn(question="Are you in Harda, Madhya Pradesh?", answer="yes"),
        OnboardTurn(question="Your main crop is Soybean — correct?", answer="yes"),
        OnboardTurn(question="You have 3.5 acres — correct?", answer="yes"),
        OnboardTurn(question="Who is in your family?", answer="Ramesh 42 self, Sunita 38 wife, Amit 12 son"),
        OnboardTurn(question="Is any woman pregnant?", answer="no"),
    ]

    prefill = {
        "name": "Ramesh Yadav",
        "state": "Madhya Pradesh",
        "district": "Harda",
        "crop_primary": "Soybean",
        "land_acres": 3.5,
    }

    result = onboarding_service.extract(turns, prefill)

    assert result["household"]["name"] == "Ramesh Yadav"
    assert result["household"]["district"] == "Harda"
    assert result["household"]["crop_primary"] == "Soybean"
    assert len(result["household"]["family_members"]) >= 2
