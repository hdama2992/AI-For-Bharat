"""
Pest Vision Router
- Analyze crop images for pest/disease detection
- Uses Claude Vision for image analysis

Returns the format expected by the frontend:
  disease_identified, severity (Low/Medium/High), confidence_pct,
  primary_cause, treatment{}, alternative_treatment{}, prevention_tips[],
  household_safety_alert (optional), sources[]
"""
from __future__ import annotations

import base64
import json
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional

from app.services.bedrock import bedrock_service
from app.db.memory import get_household

router = APIRouter(prefix="/pest", tags=["Pest Vision"])


PEST_ANALYSIS_PROMPT = """You are an expert agricultural AI for Indian farming. Analyze the crop image and respond with ONLY valid JSON:
{
  "disease_identified": "Name of pest or disease",
  "confidence_pct": 85,
  "severity": "Low | Medium | High",
  "primary_cause": "Fungal / Bacterial / Viral / Insect / Nutrient deficiency",
  "treatment": {
    "recommended_pesticide": "Product name",
    "active_ingredient": "Chemical name",
    "dosage": "e.g. 2ml/litre water",
    "frequency": "e.g. Spray twice at 10-day interval",
    "application_method": "Foliar spray",
    "cost_estimate_inr": 450,
    "safety_interval_days": 14
  },
  "alternative_treatment": {
    "name": "Neem-based alternative",
    "dosage": "5ml Neem oil/litre water",
    "cost_estimate_inr": 200
  },
  "prevention_tips": ["Tip 1", "Tip 2", "Tip 3"],
  "sources": ["ICAR", "KVK Advisory"]
}

RULES: Always include a Neem/organic alternative. Dosages must be specific. Never recommend banned pesticides."""


DANGEROUS_CHEMICALS = [
    "chlorpyrifos", "malathion", "endosulfan", "monocrotophos",
    "carbofuran", "phorate", "methyl parathion", "dimethoate",
]


def _get_safety_alert(household_id: str, pesticide_name: str) -> str | None:
    hh = get_household(household_id)
    if not hh:
        return None
    pregnant_members = [m for m in hh.family_members if m.is_pregnant]
    if not pregnant_members:
        return None
    is_dangerous = any(chem in pesticide_name.lower() for chem in DANGEROUS_CHEMICALS)
    if not is_dangerous:
        return None
    names = ", ".join(m.name for m in pregnant_members)
    return (
        f"WARNING: {names} is pregnant in your household. "
        f"{pesticide_name} contains chemicals harmful during pregnancy. "
        f"Use the recommended Neem-based organic alternative instead. "
        f"Keep all family members away during any pesticide application."
    )


@router.post("/analyze")
async def analyze_crop_image(
    image: UploadFile = File(...),
    crop_type: str = Form("Soybean"),
    household_id: str = Form(""),
    symptoms_description: str = Form(""),
):
    contents = await image.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large. Max 10MB.")

    content_type = image.content_type or "image/jpeg"
    if content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        content_type = "image/jpeg"

    image_b64 = base64.standard_b64encode(contents).decode("utf-8")

    crop_context = f"Crop type: {crop_type}."
    if symptoms_description:
        crop_context += f" Farmer's description: {symptoms_description}"

    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", "media_type": content_type, "data": image_b64}},
            {"type": "text", "text": f"{crop_context}\n\nAnalyze this crop image. Respond with ONLY the JSON."},
        ],
    }]

    response = bedrock_service.invoke(
        messages=messages,
        system_prompt=PEST_ANALYSIS_PROMPT,
        max_tokens=1024,
        temperature=0.3,
    )

    # Parse JSON
    try:
        raw = response.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
        result = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        result = {
            "disease_identified": "Analysis inconclusive",
            "confidence_pct": 0,
            "severity": "Low",
            "primary_cause": "Unable to parse AI response",
            "treatment": {
                "recommended_pesticide": "Visit your nearest KVK for in-person diagnosis",
                "active_ingredient": "N/A",
                "dosage": "N/A",
                "frequency": "N/A",
                "application_method": "N/A",
                "cost_estimate_inr": 0,
                "safety_interval_days": 0,
            },
            "alternative_treatment": None,
            "prevention_tips": ["Take clear close-up photos of affected leaves", "Visit nearest Krishi Vigyan Kendra"],
            "sources": ["ICAR"],
        }

    # Household safety cross-check
    if household_id:
        pesticide = (result.get("treatment") or {}).get("recommended_pesticide", "")
        alert = _get_safety_alert(household_id, pesticide)
        if alert:
            result["household_safety_alert"] = alert

    return result

