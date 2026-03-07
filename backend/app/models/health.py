"""
Health and Triage models
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum


class TriageLevel(str, Enum):
    """Triage severity levels following ICMR guidelines"""
    GREEN = "GREEN"   # Home care with monitoring
    YELLOW = "YELLOW" # Visit PHC/clinic within 24 hours
    RED = "RED"       # Emergency - call 108 / go to hospital NOW


class TriageResult(BaseModel):
    """Health triage assessment result"""
    triage_level: TriageLevel
    confidence_pct: int = Field(ge=0, le=100)
    assessment_summary: str
    assessment_summary_hi: Optional[str] = None
    immediate_actions: List[str]
    immediate_actions_hi: Optional[List[str]] = None
    follow_up: Optional[str] = None
    follow_up_hi: Optional[str] = None
    emergency_number: Optional[str] = None  # 108, 102, etc.
    nearest_facility: Optional[str] = None
    disclaimer: str = "This is AI-generated guidance, not a medical diagnosis. Consult a doctor for proper treatment."


class ChatMessage(BaseModel):
    """Single chat message"""
    role: Literal["user", "assistant"]
    content: str


class HealthChatRequest(BaseModel):
    """Request for health chat"""
    household_id: str
    message: str
    conversation_history: List[ChatMessage] = []
    session_id: Optional[str] = None
    language: Literal["en", "hi"] = "en"


class HealthSession(BaseModel):
    """Health consultation session with slot-filling state"""
    session_id: str
    household_id: str
    messages: List[ChatMessage] = []
    slots: dict = {}  # Collected symptoms info
    triage_result: Optional[TriageResult] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Slot-filling slots to collect
    # symptoms: str - Main complaint
    # duration: str - How long?
    # severity: str - How bad? (1-10 or descriptive)
    # patient_age: int - Age of patient
    # patient_gender: str - Gender
    # is_pregnant: bool - Is pregnant?
    # medical_history: List[str] - Existing conditions


class SymptomSlots(BaseModel):
    """Required slots for health triage"""
    symptoms: Optional[str] = None
    duration: Optional[str] = None
    severity: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    is_pregnant: Optional[bool] = None
    medical_history: List[str] = []
    temperature: Optional[str] = None  # "102F", "high", etc.
    other_symptoms: List[str] = []

