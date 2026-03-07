"""
In-memory database for prototype
Replace with DynamoDB for production
"""
from typing import Dict, Optional
from datetime import datetime
import uuid

from app.models.household import Household, FamilyMember
from app.models.health import HealthSession


# In-memory stores
HOUSEHOLDS: Dict[str, Household] = {}
HEALTH_SESSIONS: Dict[str, HealthSession] = {}


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


# Initialize demo data on module load
init_demo_data()

