"""
Mandi (Market) Price Comparison Router
Uses mock data for prototype - would connect to e-NAM API in production
"""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.models.mandi import MandiPrice, MandiCompareResponse

router = APIRouter(prefix="/mandi", tags=["Mandi"])

# Load mock data
DATA_DIR = Path(__file__).parent.parent.parent / "data"

def load_json(filename: str) -> dict:
    with open(DATA_DIR / filename) as f:
        return json.load(f)


# Transport cost: ₹3 per km per quintal (diesel, labor, time)
TRANSPORT_COST_PER_KM = 3.0


@router.get("/crops")
async def get_crops():
    """Get list of available crops"""
    data = load_json("crops.json")
    return {"crops": [c["name"] for c in data["crops"]]}


@router.get("/districts")
async def get_districts():
    """Get list of available districts"""
    data = load_json("districts.json")
    return {"districts": [d["name"] for d in data["districts"]]}


@router.get("/compare", response_model=MandiCompareResponse)
async def compare_mandi_prices(
    crop: str = Query(..., description="Crop name"),
    district: str = Query(..., description="Home district"),
    household_id: Optional[str] = Query(None, description="Household ID for context"),
    quantity_quintals: float = Query(10.0, description="Quantity in quintals"),
):
    """Compare prices across Mandis for a crop"""
    
    # Load data
    mandi_data = load_json("mandi_prices.json")
    crops_data = load_json("crops.json")
    
    # Find crop info
    crop_info = next((c for c in crops_data["crops"] if c["name"].lower() == crop.lower()), None)
    if not crop_info:
        raise HTTPException(status_code=404, detail=f"Crop '{crop}' not found")
    
    # Get prices for this crop
    crop_prices = mandi_data.get(crop)
    if not crop_prices:
        raise HTTPException(status_code=404, detail=f"No price data for '{crop}'")
    
    # Find home mandi
    home_data = crop_prices.get(district)
    if not home_data:
        # Use first available as fallback
        district = list(crop_prices.keys())[0]
        home_data = crop_prices[district]
    
    home_mandi = MandiPrice(
        mandi_name=home_data["mandi_name"],
        mandi_name_hi=home_data["mandi_name_hi"],
        district=district,
        state=home_data["state"],
        modal_price=home_data["modal_price"],
        min_price=home_data.get("min_price"),
        max_price=home_data.get("max_price"),
        distance_km=0,
        transport_cost=0,
        net_gain=0,
        last_updated=datetime.utcnow(),
    )
    
    # Calculate alternatives
    alternatives = []
    home_price = home_data["modal_price"]
    
    for mandi_district, data in crop_prices.items():
        if mandi_district == district:
            continue
        
        distance = data["distance_km"]
        transport_cost = distance * TRANSPORT_COST_PER_KM
        net_gain = data["modal_price"] - home_price - transport_cost
        
        alternatives.append(MandiPrice(
            mandi_name=data["mandi_name"],
            mandi_name_hi=data["mandi_name_hi"],
            district=mandi_district,
            state=data["state"],
            modal_price=data["modal_price"],
            min_price=data.get("min_price"),
            max_price=data.get("max_price"),
            distance_km=distance,
            transport_cost=transport_cost,
            net_gain=net_gain,
            last_updated=datetime.utcnow(),
        ))
    
    # Sort by net gain
    alternatives.sort(key=lambda x: x.net_gain, reverse=True)
    
    # Find best mandi
    best = alternatives[0] if alternatives and alternatives[0].net_gain > 0 else None
    best_mandi_name = best.mandi_name if best else home_mandi.mandi_name
    
    # Calculate potential savings
    potential_savings = 0
    if best and best.net_gain > 0:
        potential_savings = best.net_gain * quantity_quintals
    
    # Generate recommendation
    if potential_savings > 500:
        recommendation = f"Sell at {best_mandi_name} to earn ₹{int(potential_savings)} extra on {int(quantity_quintals)} quintals!"
        recommendation_hi = f"{int(quantity_quintals)} क्विंटल पर ₹{int(potential_savings)} ज्यादा कमाने के लिए {best.mandi_name_hi if best else ''} में बेचें!"
    else:
        recommendation = f"Sell locally at {home_mandi.mandi_name}. Transport costs make other mandis uneconomical."
        recommendation_hi = f"स्थानीय {home_mandi.mandi_name_hi} में बेचें। दूसरी मंडियों में ले जाने का खर्चा ज्यादा है।"
    
    return MandiCompareResponse(
        crop=crop,
        crop_hi=crop_info["name_hi"],
        msp_price=crop_info["msp_2025"],
        home_mandi=home_mandi,
        alternatives=alternatives,
        best_mandi=best_mandi_name,
        potential_savings=potential_savings,
        recommendation=recommendation,
        recommendation_hi=recommendation_hi,
    )

