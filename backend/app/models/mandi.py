"""
Mandi (Market) price models
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class MandiPrice(BaseModel):
    """Price at a specific Mandi"""
    mandi_name: str
    mandi_name_hi: str
    district: str
    state: str
    modal_price: float  # Most common trading price (₹/quintal)
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    distance_km: float
    transport_cost: float  # ₹ per quintal
    net_gain: float  # modal_price - transport_cost relative to home
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class MandiCompareRequest(BaseModel):
    """Request for Mandi price comparison"""
    crop: str
    district: str
    household_id: Optional[str] = None
    quantity_quintals: float = 10.0  # Default 10 quintals


class MandiCompareResponse(BaseModel):
    """Response with Mandi comparisons"""
    crop: str
    crop_hi: str
    msp_price: float  # Minimum Support Price
    home_mandi: MandiPrice
    alternatives: List[MandiPrice]
    best_mandi: str
    potential_savings: float  # Total extra earnings at best mandi
    recommendation: str
    recommendation_hi: str


class CropInfo(BaseModel):
    """Crop information"""
    name: str
    name_hi: str
    msp_2025: float  # MSP for 2025-26 in ₹/quintal
    season: str  # kharif, rabi, zaid

