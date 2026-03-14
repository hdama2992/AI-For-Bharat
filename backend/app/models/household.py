"""
Household and Family models
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class FamilyMember(BaseModel):
    """Individual family member"""
    name: str
    age: int
    relation: str  # self, spouse, child, parent, etc.
    gender: Optional[str] = None
    is_pregnant: bool = False
    chronic_conditions: List[str] = []  # diabetes, hypertension, etc.


class Household(BaseModel):
    """Household profile"""
    household_id: str
    name: str = "Unknown"
    phone: Optional[str] = None
    state: str = "Unknown"
    district: str = "Unknown"
    village: Optional[str] = None
    crop_primary: Optional[str] = None
    crop_secondary: Optional[str] = None
    land_acres: Optional[float] = None
    family_members: List[FamilyMember] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class HouseholdCreate(BaseModel):
    """Request model for creating household"""
    name: Optional[str] = "Unknown"
    phone: Optional[str] = None
    state: Optional[str] = "Unknown"
    district: Optional[str] = "Unknown"
    village: Optional[str] = None
    crop_primary: Optional[str] = None
    crop_secondary: Optional[str] = None
    land_acres: Optional[float] = None
    family_members: List[FamilyMember] = []


class HouseholdResponse(BaseModel):
    """Response model for household"""
    household_id: str
    name: str = "Unknown"
    phone: Optional[str] = None
    state: str = "Unknown"
    district: str = "Unknown"
    village: Optional[str] = None
    crop_primary: Optional[str] = None
    crop_secondary: Optional[str] = None
    land_acres: Optional[float] = None
    family_members: List[FamilyMember] = []


class OnboardTurn(BaseModel):
    """Single Q&A turn from voice onboarding"""
    question: str
    answer: str


class OnboardExtractRequest(BaseModel):
    """Request to extract household data from voice conversation"""
    turns: List[OnboardTurn]
    prefill: dict = {}  # Pre-filled data from PM-KISAN etc.


class OnboardExtractResponse(BaseModel):
    """Response from AI extraction"""
    household: dict
    confidence: float  # 0-1
    missing_fields: List[str]


class ContextInsight(BaseModel):
    """Contextual insight for dashboard"""
    type: str  # mandi_alert, health_tip, weather, scheme
    title: str
    title_hi: str
    description: str
    description_hi: str
    priority: int = 0  # higher = more important
    action_url: Optional[str] = None

