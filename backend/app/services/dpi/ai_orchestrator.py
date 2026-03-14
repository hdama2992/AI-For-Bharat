"""
AI Orchestrator for DPI Integration - Uses AWS Bedrock to map natural language to DPI API parameters.

This orchestrator:
1. Takes user voice/text input + household context
2. Uses Claude (Haiku for speed) to extract intent and parameters
3. Routes to appropriate DPI service (AGMARKNET, ABDM HFR, etc.)
4. Returns structured response for TTS synthesis
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from enum import Enum

from app.services.bedrock import bedrock_service
from app.config import get_settings

settings = get_settings()


class DPIService(str, Enum):
    """Available DPI services."""
    MANDI = "mandi"           # AGMARKNET - Mandi prices
    HEALTH_FACILITY = "health_facility"  # ABDM HFR - Hospitals/PHCs/Pharmacies
    JAN_AUSHADHI = "jan_aushadhi"  # Generic medicine stores
    TRANSPORT = "transport"   # Dhwani - Goods transport to mandi
    NONE = "none"             # No DPI service needed


# System prompt for intent classification and parameter extraction
ORCHESTRATOR_SYSTEM_PROMPT = """You are an AI assistant for Indian farmers. Your job is to:
1. Understand the user's request (in Hindi, English, or Hinglish)
2. Determine which DPI (Digital Public Infrastructure) service to query
3. Extract the relevant parameters from the request + household context

Available DPI Services:
- mandi: For crop prices, mandi rates, where to sell crops
- health_facility: For finding hospitals, PHCs, clinics nearby
- jan_aushadhi: For finding Jan Aushadhi Kendra (generic/cheap medicine stores)
- transport: For goods transport cost to mandi, logistics queries
- none: For general questions, greetings, or non-DPI queries

User's Household Context (use this to fill missing parameters):
{household_context}

RESPOND ONLY WITH VALID JSON in this exact format:
{{
    "service": "mandi|health_facility|jan_aushadhi|transport|none",
    "confidence": 0.0-1.0,
    "parameters": {{
        // For mandi:
        "commodity": "crop name in English",
        "state": "state name",
        "district": "district name"

        // For health_facility:
        "facility_type": "hospital|phc|clinic|any",
        "specialty": "general|pulmonology|cardiology|gynecology|pediatrics|orthopedics|any",
        "state": "state name",
        "district": "district name",
        "urgency": "routine|urgent|emergency"

        // For jan_aushadhi:
        "state": "state name",
        "district": "district name"

        // For transport:
        "to_mandi": "destination mandi name",
        "quantity_quintals": number,
        "commodity": "crop being transported"
    }},
    "extracted_intent": "brief description of what user wants",
    "fallback_response": "response if service unavailable (in same language as input)"
}}

Examples:
- "सोयाबीन का भाव क्या है?" → service: mandi, commodity: soybean
- "पास में कोई अस्पताल बताओ" → service: health_facility, facility_type: hospital
- "मेरी बीवी को प्रेग्नेंसी चेकअप करवाना है" → service: health_facility, specialty: gynecology
- "जन औषधि केंद्र कहाँ है?" → service: jan_aushadhi
- "सस्ती दवाई कहाँ मिलेगी?" → service: jan_aushadhi
- "मंडी तक माल पहुंचाने में कितना खर्चा आएगा?" → service: transport
- "10 क्विंटल सोयाबीन भोपाल भेजना है" → service: transport, to_mandi: bhopal, quantity: 10
- "नमस्ते" → service: none
"""


class DPIOrchestrator:
    """Orchestrates DPI service calls using AI for intent classification and parameter extraction."""
    
    def __init__(self):
        self.bedrock = bedrock_service
    
    def classify_and_extract(
        self,
        user_message: str,
        household_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Use Bedrock (Claude Haiku for speed) to classify intent and extract parameters.
        
        Args:
            user_message: User's input in any language
            household_context: Dict with name, district, state, crop_primary, family_members
            
        Returns:
            Dict with service, confidence, parameters, extracted_intent, fallback_response
        """
        if not self.bedrock.is_configured():
            return self._fallback_classification(user_message, household_context)
        
        # Build context string
        context_str = "None provided"
        if household_context:
            context_str = json.dumps({
                "name": household_context.get("name", ""),
                "state": household_context.get("state", "Madhya Pradesh"),
                "district": household_context.get("district", "Harda"),
                "primary_crop": household_context.get("crop_primary", "Soybean"),
                "family_members": len(household_context.get("family_members", [])),
            }, ensure_ascii=False)
        
        system_prompt = ORCHESTRATOR_SYSTEM_PROMPT.format(household_context=context_str)
        
        messages = [{"role": "user", "content": user_message}]
        
        try:
            # Use Haiku for fast classification
            response = self.bedrock.invoke_haiku(messages, system_prompt=system_prompt)
            
            # Parse JSON response
            result = self._parse_json_response(response)
            
            # Enrich with household context if parameters are missing
            if household_context:
                result = self._enrich_with_context(result, household_context)
            
            return result
            
        except Exception as e:
            print(f"AI Orchestrator error: {e}")
            return self._fallback_classification(user_message, household_context)
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Remove markdown code blocks if present
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object in response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
            raise
    
    def _enrich_with_context(self, result: Dict, context: Dict) -> Dict:
        """Fill missing parameters from household context."""
        params = result.get("parameters", {})
        
        # Fill location if missing
        if not params.get("state"):
            params["state"] = context.get("state", "Madhya Pradesh")
        if not params.get("district"):
            params["district"] = context.get("district", "Harda")
        
        # Fill commodity from primary crop if mandi service and not specified
        if result.get("service") == "mandi" and not params.get("commodity"):
            params["commodity"] = context.get("crop_primary", "Soybean")
        
        result["parameters"] = params
        return result
    
    def _fallback_classification(self, message: str, context: Optional[Dict]) -> Dict:
        """Simple keyword-based fallback when Bedrock unavailable."""
        msg_lower = message.lower()

        # Keywords for each service
        mandi_keywords = ["mandi", "bhav", "भाव", "price", "rate", "बेचना", "sell", "मंडी"]
        health_keywords = ["hospital", "doctor", "अस्पताल", "डॉक्टर", "phc", "clinic", "health", "बीमार", "sick", "allergy"]
        jan_aushadhi_keywords = ["jan aushadhi", "जन औषधि", "generic", "sasti dawai", "सस्ती दवाई", "cheap medicine", "aushadhi kendra"]
        transport_keywords = ["transport", "ट्रांसपोर्ट", "truck", "ट्रक", "गाड़ी", "माल भेजना", "le jana", "pahunchana", "पहुंचाना", "किराया", "freight"]

        # Determine service (order matters - more specific first)
        service = DPIService.NONE
        if any(kw in msg_lower for kw in jan_aushadhi_keywords):
            service = DPIService.JAN_AUSHADHI
        elif any(kw in msg_lower for kw in transport_keywords):
            service = DPIService.TRANSPORT
        elif any(kw in msg_lower for kw in mandi_keywords):
            service = DPIService.MANDI
        elif any(kw in msg_lower for kw in health_keywords):
            service = DPIService.HEALTH_FACILITY

        # Build default parameters from context
        params = {}
        if context:
            params["state"] = context.get("state", "Madhya Pradesh")
            params["district"] = context.get("district", "Harda")
            if service == DPIService.MANDI:
                params["commodity"] = context.get("crop_primary", "Soybean")
            elif service == DPIService.HEALTH_FACILITY:
                params["facility_type"] = "any"
                params["specialty"] = "any"
                params["urgency"] = "routine"
            elif service == DPIService.TRANSPORT:
                params["commodity"] = context.get("crop_primary", "Soybean")
                params["quantity_quintals"] = 10  # Default estimate

        return {
            "service": service.value,
            "confidence": 0.5,
            "parameters": params,
            "extracted_intent": f"User query about {service.value}",
            "fallback_response": "Please provide more details about what you need."
        }


# ============================================================================
# EVIDENCE-FIRST SLOT-FILLING DEFINITIONS
# ============================================================================

# Required slots for each DPI service - based on design.md Evidence Checklist
SLOT_DEFINITIONS = {
    DPIService.MANDI: {
        "required": ["commodity", "district"],
        "optional": ["state", "quantity_quintal"],
        "questions": {
            "commodity": {
                "en": "Which crop would you like to check prices for?",
                "hi": "आप किस फसल का भाव जानना चाहते हैं?"
            },
            "district": {
                "en": "Which district are you located in?",
                "hi": "आप किस जिले में हैं?"
            }
        }
    },
    DPIService.HEALTH_FACILITY: {
        "required": ["facility_type", "district"],
        "optional": ["state", "specialty", "urgency"],
        "questions": {
            "facility_type": {
                "en": "What type of facility do you need? (Hospital, Clinic, PHC)",
                "hi": "आपको किस प्रकार की सुविधा चाहिए? (अस्पताल, क्लीनिक, PHC)"
            },
            "district": {
                "en": "Which district should I search in?",
                "hi": "मैं किस जिले में खोजूं?"
            },
            "specialty": {
                "en": "Do you need a specific specialty? (General, Eye, Heart, Women's health, Children)",
                "hi": "क्या आपको किसी विशेष विभाग की जरूरत है? (सामान्य, आंख, दिल, महिला स्वास्थ्य, बच्चे)"
            }
        }
    },
    DPIService.JAN_AUSHADHI: {
        "required": ["district"],
        "optional": ["state"],
        "questions": {
            "district": {
                "en": "Which district should I search for Jan Aushadhi Kendra?",
                "hi": "मैं किस जिले में जन औषधि केंद्र खोजूं?"
            }
        }
    },
    DPIService.TRANSPORT: {
        "required": ["to_mandi", "quantity_quintals"],
        "optional": ["commodity", "from_location"],
        "questions": {
            "to_mandi": {
                "en": "Which mandi do you want to transport your goods to?",
                "hi": "आप किस मंडी में माल भेजना चाहते हैं?"
            },
            "quantity_quintals": {
                "en": "How many quintals do you want to transport?",
                "hi": "आप कितने क्विंटल माल भेजना चाहते हैं?"
            }
        }
    }
}


class SlotFillingOrchestrator:
    """
    Evidence-First Slot-Filling Orchestrator.

    Follows the pattern from design.md:
    1. Identify missing required slots
    2. Ask ONE clarifying question at a time
    3. Auto-fill from household context where possible
    4. Only call DPI API when all required slots are filled
    """

    def __init__(self):
        self.bedrock = bedrock_service
        self.classifier = DPIOrchestrator()

    def process_turn(
        self,
        user_message: str,
        current_slots: Dict[str, Any],
        household_context: Optional[Dict[str, Any]] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Process a conversation turn with Evidence-First Slot-Filling.

        Returns:
            {
                "service": DPIService,
                "slots": Dict[str, Any],
                "slots_complete": bool,
                "missing_slots": List[str],
                "clarifying_question": Optional[str],
                "ready_for_api": bool,
                "api_params": Optional[Dict]
            }
        """
        # Step 1: Classify intent and extract parameters
        classification = self.classifier.classify_and_extract(user_message, household_context)
        service_str = classification.get("service", "none")

        try:
            service = DPIService(service_str)
        except ValueError:
            service = DPIService.NONE

        # Step 2: Merge extracted params with existing slots
        extracted_params = classification.get("parameters", {})
        merged_slots = {**current_slots, **extracted_params}

        # Step 3: Auto-fill from household context
        if household_context:
            merged_slots = self._auto_fill_from_context(service, merged_slots, household_context)

        # Step 4: Check for missing required slots
        slot_def = SLOT_DEFINITIONS.get(service)
        if not slot_def:
            return {
                "service": service,
                "slots": merged_slots,
                "slots_complete": True,
                "missing_slots": [],
                "clarifying_question": None,
                "ready_for_api": False,  # No API for NONE service
                "api_params": None,
                "classification": classification
            }

        missing_slots = self._find_missing_slots(merged_slots, slot_def["required"])

        # Step 5: If slots missing, ask ONE clarifying question
        if missing_slots:
            first_missing = missing_slots[0]
            question = slot_def["questions"].get(first_missing, {}).get(
                language,
                f"Please provide the {first_missing}."
            )
            return {
                "service": service,
                "slots": merged_slots,
                "slots_complete": False,
                "missing_slots": missing_slots,
                "clarifying_question": question,
                "ready_for_api": False,
                "api_params": None,
                "classification": classification
            }

        # Step 6: All slots filled - ready for API
        return {
            "service": service,
            "slots": merged_slots,
            "slots_complete": True,
            "missing_slots": [],
            "clarifying_question": None,
            "ready_for_api": True,
            "api_params": self._build_api_params(service, merged_slots),
            "classification": classification
        }

    def _auto_fill_from_context(
        self,
        service: DPIService,
        slots: Dict,
        context: Dict
    ) -> Dict:
        """Auto-fill slots from household context (onboarding data)."""
        filled = slots.copy()

        # Location is common to all services
        if not filled.get("state"):
            filled["state"] = context.get("state")
        if not filled.get("district"):
            filled["district"] = context.get("district")

        # Service-specific auto-fill
        if service == DPIService.MANDI:
            if not filled.get("commodity"):
                filled["commodity"] = context.get("crop_primary")

        return filled

    def _find_missing_slots(self, slots: Dict, required: List[str]) -> List[str]:
        """Find which required slots are missing or empty."""
        missing = []
        for slot_name in required:
            value = slots.get(slot_name)
            if value is None or value == "" or value == "any":
                # "any" is treated as unfilled for facility_type
                if slot_name == "facility_type" and value == "any":
                    continue  # Accept "any" for facility_type
                elif not value:
                    missing.append(slot_name)
        return missing

    def _build_api_params(self, service: DPIService, slots: Dict) -> Dict:
        """Build API parameters from filled slots."""
        if service == DPIService.MANDI:
            return {
                "crop": slots.get("commodity"),
                "district": slots.get("district"),
                "state": slots.get("state", "Madhya Pradesh")
            }
        elif service == DPIService.HEALTH_FACILITY:
            return {
                "facility_type": slots.get("facility_type", "any"),
                "district": slots.get("district"),
                "state": slots.get("state", "Madhya Pradesh"),
                "specialty": slots.get("specialty"),
                "urgency": slots.get("urgency", "routine")
            }
        elif service == DPIService.JAN_AUSHADHI:
            return {
                "district": slots.get("district"),
                "state": slots.get("state", "Madhya Pradesh")
            }
        elif service == DPIService.TRANSPORT:
            return {
                "to_mandi": slots.get("to_mandi"),
                "quantity_quintals": slots.get("quantity_quintals", 10),
                "commodity": slots.get("commodity"),
                "from_location": slots.get("from_location", slots.get("district"))
            }
        return {}


# Singleton instances
dpi_orchestrator = DPIOrchestrator()
slot_filling_orchestrator = SlotFillingOrchestrator()

