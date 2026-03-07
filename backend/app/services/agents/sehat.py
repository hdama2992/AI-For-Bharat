"""
Sehat (Health) Agent - Health Triage with Slot-Filling
"""
import json
import re
from typing import Generator, Optional, Dict, List

from app.services.bedrock import bedrock_service
from app.services.agents.prompts import SEHAT_AGENT_SYSTEM_PROMPT
from app.models.health import TriageResult, TriageLevel, ChatMessage


class SehatAgent:
    """Health triage agent using Claude with slot-filling"""
    
    def __init__(self):
        self.system_prompt = SEHAT_AGENT_SYSTEM_PROMPT
    
    def _format_messages(
        self,
        user_message: str,
        conversation_history: List[ChatMessage],
        household_context: Optional[Dict] = None,
    ) -> List[Dict]:
        """Format messages for Claude API"""
        messages = []
        
        # Add context about household if available
        if household_context:
            context_msg = self._build_context_message(household_context)
            messages.append({"role": "user", "content": f"[CONTEXT: {context_msg}]"})
            messages.append({"role": "assistant", "content": "I understand. I'll keep this context in mind while helping with health concerns."})
        
        # Add conversation history
        for msg in conversation_history:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _build_context_message(self, household: Dict) -> str:
        """Build context string from household data"""
        parts = [f"Family: {household.get('name', 'Unknown')}"]
        
        if household.get("family_members"):
            members = household["family_members"]
            parts.append(f"Members: {len(members)} people")
            
            # Note any health-relevant info
            for m in members:
                if isinstance(m, dict):
                    if m.get("is_pregnant"):
                        parts.append(f"- {m.get('name', 'Someone')} is pregnant")
                    if m.get("chronic_conditions"):
                        parts.append(f"- {m.get('name', 'Someone')} has: {', '.join(m['chronic_conditions'])}")
        
        return "; ".join(parts)
    
    def chat_stream(
        self,
        user_message: str,
        conversation_history: List[ChatMessage],
        household_context: Optional[Dict] = None,
        language: str = "en",
    ) -> Generator[str, None, None]:
        """Stream chat response from Claude"""
        messages = self._format_messages(user_message, conversation_history, household_context)
        
        # Add language preference to system prompt
        lang_note = "\n\nUser's preferred language: " + ("Hindi (respond primarily in Hindi with English)" if language == "hi" else "English (with Hindi translations)")
        system = self.system_prompt + lang_note
        
        # Stream response
        for chunk in bedrock_service.invoke_stream(
            messages=messages,
            system_prompt=system,
            max_tokens=1500,
            temperature=0.7,
        ):
            yield chunk
    
    def extract_triage(self, full_response: str) -> Optional[TriageResult]:
        """Extract triage JSON from response if present"""
        # Look for <TRIAGE>...</TRIAGE> block
        match = re.search(r'<TRIAGE>\s*(\{[\s\S]*?\})\s*</TRIAGE>', full_response)
        
        if not match:
            return None
        
        try:
            data = json.loads(match.group(1))
            
            # Map to TriageResult
            level = data.get("triage_level", "GREEN").upper()
            if level not in ["GREEN", "YELLOW", "RED"]:
                level = "GREEN"
            
            return TriageResult(
                triage_level=TriageLevel(level),
                confidence_pct=min(100, max(0, int(data.get("confidence_pct", 70)))),
                assessment_summary=data.get("assessment_summary", "Assessment provided."),
                immediate_actions=data.get("immediate_actions", []),
                follow_up=data.get("follow_up"),
                emergency_number=data.get("emergency_number") if level == "RED" else None,
                disclaimer=data.get("disclaimer", "This is AI guidance, not a diagnosis. Always consult a doctor."),
            )
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to parse triage JSON: {e}")
            return None


# Singleton
sehat_agent = SehatAgent()

