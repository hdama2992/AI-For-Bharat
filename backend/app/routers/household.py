"""
Household API Router
- Create/Get household profiles
- AI extraction from voice onboarding
- Context insights
"""
from fastapi import APIRouter, HTTPException

from app.models.household import (
    HouseholdCreate,
    HouseholdResponse,
    OnboardExtractRequest,
    OnboardExtractResponse,
)
from app.db.memory import create_household, get_household
from app.services.onboarding import onboarding_service

router = APIRouter(prefix="/household", tags=["Household"])


@router.post("", response_model=dict)
async def create_household_endpoint(data: HouseholdCreate):
    """Create a new household profile"""
    household = create_household(data.model_dump())
    return {"household_id": household.household_id}


@router.get("/{household_id}", response_model=HouseholdResponse)
async def get_household_endpoint(household_id: str):
    """Get household by ID"""
    household = get_household(household_id)
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")
    return household


@router.post("/onboard-extract", response_model=OnboardExtractResponse)
async def extract_onboarding_data(request: OnboardExtractRequest):
    """Extract structured household data from voice conversation turns using AI"""
    data = onboarding_service.extract(request.turns, request.prefill)
    return OnboardExtractResponse(
        household=data.get("household", {}),
        confidence=data.get("confidence", 0.7),
        missing_fields=data.get("missing_fields", []),
    )


@router.get("/context/{household_id}")
async def get_context_insights(household_id: str):
    """Get contextual insights for household dashboard

    Returns format expected by frontend HouseholdContextBanner component
    """
    household = get_household(household_id)
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")

    insights = []

    # Mandi alert based on crop
    if household.crop_primary:
        insights.append({
            "type": "mandi_alert",
            "severity": "warning",
            "module_trigger": "mandi",
            "icon": "rupee",
            "message_en": f"📈 {household.crop_primary} prices rising in Bhopal - ₹270/quintal higher!",
            "message_hi": f"📈 भोपाल में {household.crop_primary} के दाम बढ़े - ₹270/क्विंटल ज्यादा!",
            "action_en": "Check Mandi Advisor for best selling price",
            "action_hi": "मंडी सलाहकार में सबसे अच्छा भाव देखें",
        })

    # Health tip - seasonal
    insights.append({
        "type": "health_tip",
        "severity": "info",
        "module_trigger": "health",
        "icon": "shield",
        "message_en": "🌡️ Dengue season alert - use mosquito nets",
        "message_hi": "🌡️ डेंगू का मौसम - मच्छरदानी लगाएं",
        "action_en": "Remove standing water around home",
        "action_hi": "घर के आसपास जमा पानी हटाएं",
    })

    # Check for pregnant family members
    for member in household.family_members:
        if member.is_pregnant:
            insights.insert(0, {
                "type": "pregnancy_care",
                "severity": "critical",
                "module_trigger": "health",
                "icon": "heart",
                "message_en": f"🤰 Pregnancy care reminder for {member.name}",
                "message_hi": f"🤰 {member.name} के लिए गर्भावस्था देखभाल",
                "action_en": "Next ANM visit due. Ensure iron tablets and folic acid.",
                "action_hi": "अगली ANM विज़िट का समय। आयरन और फोलिक एसिड लें।",
            })
            break

    # Weather info
    insights.append({
        "type": "weather",
        "severity": "info",
        "module_trigger": "dashboard",
        "icon": "calendar",
        "message_en": "☀️ Clear skies next 3 days - good for harvesting",
        "message_hi": "☀️ अगले 3 दिन साफ मौसम - कटाई के लिए अच्छा",
        "action_en": "Plan your harvest accordingly",
        "action_hi": "अपनी कटाई की योजना बनाएं",
    })

    return insights
