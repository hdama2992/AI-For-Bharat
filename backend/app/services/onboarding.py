"""
Deterministic onboarding extraction fallback for prototype reliability.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from app.models.household import OnboardTurn
from app.services.agents.prompts import ONBOARD_EXTRACTION_PROMPT
from app.services.bedrock import bedrock_service

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _load_names(filename: str, key: str) -> List[str]:
    with open(DATA_DIR / filename, encoding="utf-8") as handle:
        payload = json.load(handle)
    return [item["name"] for item in payload[key]]


KNOWN_DISTRICTS = _load_names("districts.json", "districts")
KNOWN_CROPS = _load_names("crops.json", "crops")
KNOWN_STATES = [
    "Madhya Pradesh",
    "Rajasthan",
    "Uttar Pradesh",
    "Maharashtra",
    "Telangana",
    "Bihar",
]

AFFIRMATIVE_WORDS = {"yes", "haan", "ha", "ji", "correct", "sahi", "right", "हो", "हाँ"}
NEGATIVE_WORDS = {"no", "nahi", "nahin", "गलत", "not"}
RELATION_WORDS = {
    "self": ["self", "main", "mein", "myself", "खुद"],
    "spouse": ["wife", "husband", "spouse", "पत्नी", "पति"],
    "child": ["daughter", "son", "child", "बेटी", "बेटा", "बच्चा"],
    "parent": ["mother", "father", "parent", "मां", "माता", "पिता", "father", "mother"],
}


def _normalize_answer(answer: str) -> str:
    return re.sub(r"\s+", " ", answer.strip())


def _is_affirmative(answer: str) -> bool:
    lowered = answer.lower().strip()
    return lowered in AFFIRMATIVE_WORDS


def _is_negative(answer: str) -> bool:
    lowered = answer.lower().strip()
    return lowered in NEGATIVE_WORDS


def _extract_name(answer: str, prefill: Dict[str, Any]) -> str | None:
    if _is_affirmative(answer):
        return prefill.get("name")
    cleaned = _normalize_answer(answer)
    cleaned = re.sub(r"^(my name is|i am|mein|main|mera naam|मेरा नाम)\s+", "", cleaned, flags=re.I)
    if not cleaned:
        return None
    return cleaned.title()


def _extract_state_and_district(answer: str, prefill: Dict[str, Any]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    lowered = answer.lower()
    if _is_affirmative(answer):
        if prefill.get("state"):
            result["state"] = prefill["state"]
        if prefill.get("district"):
            result["district"] = prefill["district"]
        return result

    for state in KNOWN_STATES:
        if state.lower() in lowered:
            result["state"] = state
            break

    for district in KNOWN_DISTRICTS:
        if district.lower() in lowered:
            result["district"] = district
            break

    if "district" not in result:
        parts = [part.strip() for part in re.split(r"[,/]", answer) if part.strip()]
        if parts:
            candidate = parts[0].title()
            if candidate in KNOWN_DISTRICTS:
                result["district"] = candidate
        if len(parts) > 1:
            candidate = parts[1].title()
            if candidate in KNOWN_STATES:
                result["state"] = candidate

    return result


def _extract_crop(answer: str, prefill: Dict[str, Any]) -> str | None:
    if _is_affirmative(answer):
        return prefill.get("crop_primary")
    lowered = answer.lower()
    for crop in KNOWN_CROPS:
        if crop.lower() in lowered:
            return crop
    cleaned = _normalize_answer(answer)
    return cleaned.title() if cleaned else None


def _extract_land_acres(answer: str, prefill: Dict[str, Any]) -> float | None:
    if _is_affirmative(answer):
        if prefill.get("land_acres") is not None:
            return float(prefill["land_acres"])
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", answer)
    if not match:
        return None
    value = float(match.group(1))
    if "bigha" in answer.lower():
        value *= 0.6
    return round(value, 1)


def _infer_relation(fragment: str) -> str:
    lowered = fragment.lower()
    for relation, words in RELATION_WORDS.items():
        if any(word in lowered for word in words):
            return relation
    return "other"


def _infer_gender(fragment: str, relation: str) -> str | None:
    lowered = fragment.lower()
    if any(word in lowered for word in ["female", "woman", "lady", "महिला", "wife", "mother", "daughter", "पत्नी", "मां", "बेटी"]):
        return "female"
    if any(word in lowered for word in ["male", "man", "father", "son", "पति", "पिता", "बेटा"]):
        return "male"
    if relation in {"spouse", "child", "parent"}:
        if any(word in lowered for word in ["wife", "mother", "daughter", "पत्नी", "मां", "बेटी"]):
            return "female"
        if any(word in lowered for word in ["husband", "father", "son", "पति", "पिता", "बेटा"]):
            return "male"
    return None


def _extract_family(answer: str, household_name: str | None) -> List[Dict[str, Any]]:
    family_members: List[Dict[str, Any]] = []
    segments = [segment.strip() for segment in re.split(r"[,.;\n]| and | aur ", answer, flags=re.I) if segment.strip()]

    for segment in segments:
        age_match = re.search(r"(\d{1,2})", segment)
        name_match = re.match(r"([A-Za-z\u0900-\u097f ]+)", segment)
        name = name_match.group(1).strip().title() if name_match else None
        if not name:
            continue
        relation = _infer_relation(segment)
        gender = _infer_gender(segment, relation)
        family_members.append({
            "name": name,
            "age": int(age_match.group(1)) if age_match else 30,
            "relation": relation,
            "gender": gender,
            "is_pregnant": False,
            "chronic_conditions": [],
        })

    if not family_members and household_name:
        family_members.append({
            "name": household_name,
            "age": 30,
            "relation": "self",
            "gender": None,
            "is_pregnant": False,
            "chronic_conditions": [],
        })

    return family_members


def _apply_pregnancy(answer: str, family_members: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if _is_negative(answer):
        return family_members
    if not family_members:
        return family_members

    for member in family_members:
        if member.get("gender") == "female" or member.get("relation") == "spouse":
            member["is_pregnant"] = True
            member["gender"] = member.get("gender") or "female"
            return family_members

    family_members[0]["is_pregnant"] = True
    family_members[0]["gender"] = family_members[0].get("gender") or "female"
    return family_members


def _missing_fields(household: Dict[str, Any]) -> List[str]:
    required = ["name", "state", "district", "crop_primary"]
    return [field for field in required if not household.get(field)]


def _fallback_extract(turns: List[OnboardTurn], prefill: Dict[str, Any]) -> Dict[str, Any]:
    household: Dict[str, Any] = {
        "name": prefill.get("name"),
        "phone": prefill.get("phone"),
        "state": prefill.get("state"),
        "district": prefill.get("district"),
        "village": prefill.get("village"),
        "crop_primary": prefill.get("crop_primary"),
        "crop_secondary": prefill.get("crop_secondary"),
        "land_acres": float(prefill["land_acres"]) if prefill.get("land_acres") is not None else None,
        "family_members": [],
    }

    for turn in turns:
        question = turn.question.lower()
        answer = _normalize_answer(turn.answer)
        if not answer:
            continue

        if "नाम" in question or "name" in question:
            household["name"] = _extract_name(answer, prefill) or household.get("name")
        elif "राज्य" in question or "state" in question or "district" in question or "जिले" in question:
            household.update(_extract_state_and_district(answer, prefill))
        elif "फसल" in question or "crop" in question:
            household["crop_primary"] = _extract_crop(answer, prefill) or household.get("crop_primary")
        elif "ज़मीन" in question or "land" in question or "acre" in question:
            land = _extract_land_acres(answer, prefill)
            if land is not None:
                household["land_acres"] = land
        elif "परिवार" in question or "family" in question:
            household["family_members"] = _extract_family(answer, household.get("name"))
        elif "गर्भ" in question or "pregnant" in question:
            household["family_members"] = _apply_pregnancy(answer, household.get("family_members", []))

    if not household.get("family_members") and household.get("name"):
        household["family_members"] = _extract_family(household["name"], household["name"])

    missing_fields = _missing_fields(household)
    completion = 1 - (len(missing_fields) / 4)
    confidence = round(max(0.35, min(0.92, 0.45 + (completion * 0.4))), 2)

    return {
        "household": household,
        "confidence": confidence,
        "missing_fields": missing_fields,
    }


class OnboardingService:
    """Extraction service with LLM-first, deterministic-fallback behavior."""

    def extract(self, turns: List[OnboardTurn], prefill: Dict[str, Any]) -> Dict[str, Any]:
        turns_text = "\n".join([
            f"Q: {turn.question}\nA: {turn.answer}"
            for turn in turns
        ])

        if bedrock_service.is_configured():
            prompt = f"""Extract household information from this onboarding conversation:

{turns_text}

Pre-filled data: {json.dumps(prefill)}

Return ONLY the JSON response, no other text."""
            messages = [{"role": "user", "content": prompt}]
            response = bedrock_service.invoke_haiku(messages, system_prompt=ONBOARD_EXTRACTION_PROMPT)
            try:
                raw = response.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                parsed = json.loads(raw)
                if parsed.get("household"):
                    return parsed
            except json.JSONDecodeError:
                pass

        return _fallback_extract(turns, prefill)


onboarding_service = OnboardingService()
