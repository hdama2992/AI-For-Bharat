"""
In-memory database for prototype
Replace with DynamoDB for production
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid

from app.models.household import Household, FamilyMember
from app.models.health import ChatMessage, HealthSession


# In-memory stores
HOUSEHOLDS: Dict[str, Household] = {}
HEALTH_SESSIONS: Dict[str, HealthSession] = {}
WHATSAPP_SESSIONS: Dict[str, List[ChatMessage]] = {}
WHATSAPP_MEDIA: Dict[str, dict] = {}


def init_demo_data():
    """Initialize with demo household data"""
    demo_id = "demo-rajesh-001"
    
    if demo_id not in HOUSEHOLDS:
        HOUSEHOLDS[demo_id] = Household(
            household_id=demo_id,
            name="Rajesh Kumar",
            phone="+91-9876543210",
            state="Madhya Pradesh",
            district="Harda",
            village="Khirkiya",
            crop_primary="Soybean",
            crop_secondary="Wheat",
            land_acres=5.0,
            family_members=[
                FamilyMember(name="Rajesh Kumar", age=42, relation="self", gender="male"),
                FamilyMember(name="Sunita Devi", age=38, relation="spouse", gender="female"),
                FamilyMember(name="Priya", age=16, relation="daughter", gender="female"),
                FamilyMember(name="Amit", age=12, relation="son", gender="male"),
                FamilyMember(name="Ramesh Kumar", age=68, relation="father", gender="male", chronic_conditions=["diabetes"]),
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )


# Household operations
def create_household(data: dict) -> Household:
    """Create a new household"""
    household_id = str(uuid.uuid4())[:12]
    household = Household(
        household_id=household_id,
        **data,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    HOUSEHOLDS[household_id] = household
    return household


def get_household(household_id: str) -> Optional[Household]:
    """Get household by ID"""
    return HOUSEHOLDS.get(household_id)


def update_household(household_id: str, data: dict) -> Optional[Household]:
    """Update household"""
    if household_id not in HOUSEHOLDS:
        return None
    household = HOUSEHOLDS[household_id]
    for key, value in data.items():
        if hasattr(household, key):
            setattr(household, key, value)
    household.updated_at = datetime.utcnow()
    HOUSEHOLDS[household_id] = household
    return household


# Health session operations
def create_health_session(household_id: str, session_id: str) -> HealthSession:
    """Create new health session"""
    session = HealthSession(
        session_id=session_id,
        household_id=household_id,
        messages=[],
        slots={},
        created_at=datetime.utcnow(),
    )
    key = f"{household_id}:{session_id}"
    HEALTH_SESSIONS[key] = session
    return session


def get_health_session(household_id: str, session_id: str) -> Optional[HealthSession]:
    """Get health session"""
    key = f"{household_id}:{session_id}"
    return HEALTH_SESSIONS.get(key)


def update_health_session(session: HealthSession) -> HealthSession:
    """Update health session"""
    key = f"{session.household_id}:{session.session_id}"
    HEALTH_SESSIONS[key] = session
    return session


def get_whatsapp_session(from_number: str) -> List[ChatMessage]:
    """Get recent WhatsApp conversation history for a sender."""
    return WHATSAPP_SESSIONS.get(from_number, [])


def append_whatsapp_message(from_number: str, message: ChatMessage, max_messages: int = 10) -> List[ChatMessage]:
    """Append a WhatsApp message and cap retained history."""
    history = WHATSAPP_SESSIONS.get(from_number, [])
    history.append(message)
    WHATSAPP_SESSIONS[from_number] = history[-max_messages:]
    return WHATSAPP_SESSIONS[from_number]


def clear_expired_whatsapp_media() -> None:
    """Drop expired temporary audio payloads."""
    now = datetime.utcnow()
    expired_ids = [
        media_id
        for media_id, payload in WHATSAPP_MEDIA.items()
        if payload["expires_at"] <= now
    ]
    for media_id in expired_ids:
        WHATSAPP_MEDIA.pop(media_id, None)


def store_whatsapp_media(content: bytes, content_type: str, ttl_seconds: int = 900) -> str:
    """Store temporary WhatsApp media and return its identifier."""
    clear_expired_whatsapp_media()
    media_id = str(uuid.uuid4())
    WHATSAPP_MEDIA[media_id] = {
        "content": content,
        "content_type": content_type,
        "expires_at": datetime.utcnow() + timedelta(seconds=ttl_seconds),
    }
    return media_id


def get_whatsapp_media(media_id: str) -> Optional[dict]:
    """Return temporary media if still present."""
    clear_expired_whatsapp_media()
    payload = WHATSAPP_MEDIA.get(media_id)
    if not payload:
        return None
    if payload["expires_at"] <= datetime.utcnow():
        WHATSAPP_MEDIA.pop(media_id, None)
        return None
    return payload


# Initialize demo data on module load
init_demo_data()
