"""
Shared health response generation for web chat and WhatsApp.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Generator, List, Optional

from app.models.health import ChatMessage, TriageLevel, TriageResult
from app.services.agents.sehat import sehat_agent
from app.services.bedrock import bedrock_service


RED_FLAG_TERMS = {
    "chest pain": ["chest pain", "सीने में दर्द", "heart pain"],
    "breathing": ["breathing", "breath", "shortness of breath", "सांस", "दम", "saans"],
    "unconscious": ["unconscious", "fainted", "बेहोश", "collapse"],
    "bleeding": ["bleeding", "blood loss", "खून बह", "severe bleeding"],
    "seizure": ["seizure", "fits", "झटके", "convulsion"],
    "snake bite": ["snake bite", "सांप", "snakebite"],
}
YELLOW_FLAG_TERMS = {
    "fever": ["fever", "बुखार", "temperature", "temp"],
    "vomiting": ["vomit", "vomiting", "उल्टी"],
    "stomach pain": ["stomach", " पेट", " पेट ", "abdominal", "पेट दर्द"],
    "cough": ["cough", "खांसी", "cold", "ज़ुकाम", "जुकाम"],
    "headache": ["headache", "head ache", "head pain", "सिरदर्द", "sir dard", "sar dard"],
    "weakness": ["weak", "weakness", "कमज़ोरी", "thakan", "tired"],
}
CHILD_TERMS = ["child", "daughter", "son", "baby", "kid", "बच्चा", "बेटी", "बेटा"]
ELDERLY_TERMS = ["elderly", "old", "father", "mother", "grand", "बुजुर्ग", "पिता", "मां"]
PREGNANCY_TERMS = ["pregnant", "गर्भ", "pregnancy"]


@dataclass
class HealthReply:
    """Normalized health reply for transport-specific routes."""
    display_text: str
    triage: Optional[TriageResult]
    raw_response: str
    source: str


class HealthAdvisor:
    """Reliable health guidance with LLM and deterministic fallback paths."""

    def stream_reply(
        self,
        user_message: str,
        conversation_history: List[ChatMessage],
        household_context: Optional[Dict] = None,
        language: str = "en",
    ) -> Generator[str, None, HealthReply]:
        if bedrock_service.is_configured():
            try:
                full_response = ""
                for chunk in sehat_agent.chat_stream(
                    user_message=user_message,
                    conversation_history=conversation_history,
                    household_context=household_context,
                    language=language,
                ):
                    full_response += chunk
                    yield chunk

                triage = sehat_agent.extract_triage(full_response)
                display_text = self._clean_response_text(full_response)
                if triage and not self._looks_like_transport_error(full_response):
                    return HealthReply(
                        display_text=display_text,
                        triage=triage,
                        raw_response=full_response,
                        source="bedrock",
                    )
            except Exception as exc:
                print(f"Health stream fallback triggered: {exc}")

        fallback = self.generate_reply(
            user_message=user_message,
            conversation_history=conversation_history,
            household_context=household_context,
            language=language,
        )
        for chunk in self._chunk_text(fallback.display_text):
            yield chunk
        return fallback

    def generate_reply(
        self,
        user_message: str,
        conversation_history: List[ChatMessage],
        household_context: Optional[Dict] = None,
        language: str = "en",
    ) -> HealthReply:
        if bedrock_service.is_configured():
            try:
                messages = sehat_agent._format_messages(  # noqa: SLF001 - reuse prompt shaping for prototype speed
                    user_message=user_message,
                    conversation_history=conversation_history,
                    household_context=household_context,
                )
                system = sehat_agent.system_prompt + self._language_note(language)
                full_response = bedrock_service.invoke(
                    messages=messages,
                    system_prompt=system,
                    max_tokens=1200,
                    temperature=0.4,
                )
                triage = sehat_agent.extract_triage(full_response)
                if triage and not self._looks_like_transport_error(full_response):
                    return HealthReply(
                        display_text=self._clean_response_text(full_response),
                        triage=triage,
                        raw_response=full_response,
                        source="bedrock",
                    )
            except Exception as exc:
                print(f"Health invoke fallback triggered: {exc}")

        return self._generate_fallback_reply(
            user_message=user_message,
            conversation_history=conversation_history,
            household_context=household_context,
        )

    def extract_structured_signals(
        self,
        user_message: str,
        household_context: Optional[Dict] = None,
    ) -> Dict:
        """Expose normalized health slots for session persistence and demos."""
        return self._extract_signals(user_message.lower(), household_context)

    def _generate_fallback_reply(
        self,
        user_message: str,
        conversation_history: List[ChatMessage],
        household_context: Optional[Dict],
    ) -> HealthReply:
        combined_user_text = " ".join(
            [msg.content for msg in conversation_history if msg.role == "user"] + [user_message]
        ).strip()
        lowered = combined_user_text.lower()
        signals = self._extract_signals(lowered, household_context)

        if not signals["symptoms"]:
            text = (
                "Please tell me the main symptom, who is sick, age, and how long it has been going on. "
                "For example: 'My 8-year-old daughter has fever since morning.'\n\n"
                "कृपया बताइए मुख्य तकलीफ़ क्या है, किसको है, उम्र क्या है, और कब से है। "
                "उदाहरण: 'मेरी 8 साल की बेटी को सुबह से बुखार है।'"
            )
            return HealthReply(display_text=text, triage=None, raw_response=text, source="fallback")

        if self._needs_clarification(signals, conversation_history):
            symptom_text = ", ".join(signals["symptoms"][:2])
            text = (
                f"I understand there may be {symptom_text}. Please tell me who is sick, age, temperature if any, and since when.\n\n"
                f"लग रहा है कि {symptom_text} हो सकता है। कृपया बताइए किसको है, उम्र क्या है, तापमान कितना है, और कब से है।"
            )
            return HealthReply(display_text=text, triage=None, raw_response=text, source="fallback")

        triage = self._assess_triage(signals)
        display_text = self._compose_triage_text(triage, signals)
        raw_response = f"{display_text}\n\n<TRIAGE>\n{self._serialize_triage(triage)}\n</TRIAGE>"
        return HealthReply(
            display_text=display_text,
            triage=triage,
            raw_response=raw_response,
            source="fallback",
        )

    def _extract_signals(self, lowered: str, household_context: Optional[Dict]) -> Dict:
        symptoms: List[str] = []
        for label, words in RED_FLAG_TERMS.items():
            if any(word in lowered for word in words):
                symptoms.append(label)
        for label, words in YELLOW_FLAG_TERMS.items():
            if any(word in lowered for word in words) and label not in symptoms:
                symptoms.append(label)

        age_match = re.search(r"(\d{1,2})\s*(?:year|years|yr|yrs|साल|वर्ष)", lowered)
        age = int(age_match.group(1)) if age_match else None
        if age is None:
            if any(term in lowered for term in CHILD_TERMS):
                age = 8
            elif any(term in lowered for term in ELDERLY_TERMS):
                age = 72

        temperature = None
        temp_match = re.search(r"(\d{2,3}(?:\.\d+)?)\s*°?\s*f", lowered)
        if temp_match:
            temperature = float(temp_match.group(1))
        elif "high fever" in lowered or "very high fever" in lowered:
            temperature = 103.0

        duration_days = None
        duration_match = re.search(r"(\d+)\s*(?:day|days|din|दिवस|दिन)", lowered)
        if duration_match:
            duration_days = int(duration_match.group(1))
        elif re.search(r"(\d+)\s*(?:hour|hours|hrs|hr|ghante|घंटे)", lowered):
            duration_days = 1
        elif "since morning" in lowered or "today" in lowered or "आज" in lowered:
            duration_days = 1
        elif "yesterday" in lowered or "since last" in lowered or "kal se" in lowered or "कल से" in lowered:
            duration_days = 2

        is_pregnant = any(term in lowered for term in PREGNANCY_TERMS)
        if not is_pregnant and household_context:
            is_pregnant = any(member.get("is_pregnant") for member in household_context.get("family_members", []))

        return {
            "symptoms": symptoms,
            "age": age,
            "temperature": temperature,
            "duration_days": duration_days,
            "is_pregnant": is_pregnant,
            "text": lowered,
            "is_child": age is not None and age < 12,
            "is_elderly": age is not None and age >= 70,
        }

    def _needs_clarification(self, signals: Dict, conversation_history: List[ChatMessage]) -> bool:
        red_flag_present = any(symptom in RED_FLAG_TERMS for symptom in signals["symptoms"])
        if red_flag_present:
            return False
        has_context = (
            signals["age"] is not None
            or signals["temperature"] is not None
            or signals["duration_days"] is not None
        )
        prior_user_turns = len([msg for msg in conversation_history if msg.role == "user"])
        # Don't ask for clarification if we already asked once (prior turns > 0)
        if prior_user_turns > 0:
            return False
        return not has_context

    def _assess_triage(self, signals: Dict) -> TriageResult:
        text = signals["text"]
        symptoms = signals["symptoms"]
        temp = signals["temperature"]
        duration_days = signals["duration_days"] or 0

        level = TriageLevel.GREEN
        confidence = 72
        summary = "This looks manageable at home right now, but please monitor symptoms closely."
        actions = [
            "Rest, give fluids/ORS, and light food if tolerated. / आराम करें, पानी या ORS दें, और हल्का खाना दें।",
            "Watch for worsening fever, trouble breathing, or repeated vomiting. / बुखार बढ़े, सांस में दिक्कत हो, या बार-बार उल्टी हो तो तुरंत डॉक्टर दिखाएं।",
        ]
        follow_up = "If symptoms continue beyond 24-48 hours, visit the nearest clinic. / 24-48 घंटे से ज्यादा रहे तो नजदीकी क्लिनिक जाएं।"
        emergency_number = None

        red_flag_present = any(symptom in RED_FLAG_TERMS for symptom in symptoms)
        severe_fever = temp is not None and temp >= 104
        risky_high_fever = temp is not None and temp >= 103 and (signals["is_child"] or signals["is_elderly"] or signals["is_pregnant"])
        pregnancy_red = signals["is_pregnant"] and any(word in text for word in ["bleeding", "blood", "severe pain", "खून", "तेज दर्द"])

        if red_flag_present or severe_fever or risky_high_fever or pregnancy_red:
            level = TriageLevel.RED
            confidence = 93
            summary = (
                "This needs emergency care now. The symptoms suggest a high-risk condition that should not wait. "
                "/ यह आपात स्थिति लग रही है। ऐसे लक्षणों में तुरंत अस्पताल या 108 की जरूरत हो सकती है।"
            )
            actions = [
                "Call 108 or go to the nearest hospital immediately. / अभी 108 पर कॉल करें या नजदीकी अस्पताल जाएं।",
                "Do not wait for home remedies if there is chest pain, trouble breathing, fainting, severe bleeding, or very high fever. / सीने का दर्द, सांस की दिक्कत, बेहोशी, ज्यादा खून, या बहुत तेज बुखार में घरेलू इलाज का इंतजार न करें।",
            ]
            follow_up = "Keep the patient with an adult and carry any past prescriptions if available. / मरीज को अकेला न छोड़ें और पुरानी पर्ची हो तो साथ ले जाएं।"
            emergency_number = "108"
        elif (
            "vomiting" in symptoms
            or "stomach pain" in symptoms
            or "weakness" in symptoms
            or signals["is_pregnant"]
            or signals["is_child"]
            or signals["is_elderly"]
            or duration_days >= 3
            or (temp is not None and temp >= 101)
        ):
            level = TriageLevel.YELLOW
            confidence = 84
            summary = (
                "This should be checked at a PHC or clinic soon. It does not sound like an immediate ambulance emergency, "
                "but it needs medical attention today or tomorrow. / यह PHC या क्लिनिक में जल्दी दिखाना चाहिए। "
                "अभी एम्बुलेंस जैसी इमरजेंसी नहीं लग रही, लेकिन आज या कल डॉक्टर को दिखाएं।"
            )
            actions = [
                "Visit the nearest PHC or clinic today if possible. / आज ही नजदीकी PHC या क्लिनिक जाएं।",
                "Give fluids, rest, and note fever, vomiting, pain, or weakness frequency. / पानी दें, आराम कराएं, और बुखार, उल्टी, दर्द या कमज़ोरी कितनी बार हो रही है यह नोट करें।",
            ]
            follow_up = "If breathing becomes difficult, the patient becomes drowsy, or fever goes above 103°F, call 108. / सांस में दिक्कत, बहुत सुस्ती, या 103°F से ऊपर बुखार हो तो 108 पर कॉल करें।"

        return TriageResult(
            triage_level=level,
            confidence_pct=confidence,
            assessment_summary=summary,
            immediate_actions=actions,
            follow_up=follow_up,
            emergency_number=emergency_number,
            disclaimer="This is AI guidance, not a diagnosis. Always consult a doctor. / यह AI सलाह है, पक्का इलाज नहीं। डॉक्टर से जरूर मिलें।",
        )

    def _compose_triage_text(self, triage: TriageResult, signals: Dict) -> str:
        symptom_text = ", ".join(signals["symptoms"][:3]) or "the reported symptoms"
        headline = {
            TriageLevel.GREEN: "Home care is reasonable right now. / अभी घर पर देखभाल की जा सकती है।",
            TriageLevel.YELLOW: "Please visit a PHC or clinic soon. / कृपया जल्दी PHC या क्लिनिक जाएं।",
            TriageLevel.RED: "This sounds urgent. Get emergency help now. / यह गंभीर लग रहा है। अभी आपात मदद लें।",
        }[triage.triage_level]
        actions = "\n".join([f"- {action}" for action in triage.immediate_actions])
        follow_up = triage.follow_up or ""
        return (
            f"{headline}\n\n"
            f"I am considering symptoms like {symptom_text}. / मैं {symptom_text} जैसे लक्षणों को ध्यान में रख रहा हूं।\n\n"
            f"{triage.assessment_summary}\n\n"
            f"{actions}\n\n"
            f"{follow_up}"
        ).strip()

    def _serialize_triage(self, triage: TriageResult) -> str:
        return triage.model_dump_json(indent=2)

    def _clean_response_text(self, text: str) -> str:
        return re.sub(r"<TRIAGE>[\s\S]*?</TRIAGE>", "", text).strip()

    def _chunk_text(self, text: str, chunk_size: int = 80) -> Generator[str, None, None]:
        for start in range(0, len(text), chunk_size):
            yield text[start:start + chunk_size]

    def _looks_like_transport_error(self, text: str) -> bool:
        lowered = text.lower()
        return lowered.startswith("[error") or "bedrock not configured" in lowered

    def _language_note(self, language: str) -> str:
        if language == "hi":
            return "\n\nUser prefers Hindi-first, bilingual responses."
        return "\n\nUser prefers English-first, bilingual responses."


health_advisor = HealthAdvisor()
