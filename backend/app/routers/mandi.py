"""
Mandi (Market) Price Comparison Router
Uses mock data for prototype - would connect to e-NAM API in production

Returns the flat format expected by the frontend:
  all_mandis[], best_mandi, best_net_gain, savings_message_en/hi, msp, last_updated
"""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/mandi", tags=["Mandi"])

DATA_DIR = Path(__file__).parent.parent.parent / "data"

TRANSPORT_COST_PER_KM = 3.0


def load_json(filename: str) -> dict:
    with open(DATA_DIR / filename) as f:
        return json.load(f)


@router.get("/crops")
async def get_crops():
    data = load_json("crops.json")
    return {"crops": [c["name"] for c in data["crops"]]}


@router.get("/districts")
async def get_districts():
    data = load_json("districts.json")
    return {"districts": [d["name"] for d in data["districts"]]}


@router.get("/compare")
async def compare_mandi_prices(
    crop: str = Query(...),
    district: str = Query(...),
    household_id: Optional[str] = Query(None),
):
    mandi_data = load_json("mandi_prices.json")
    crops_data = load_json("crops.json")

    crop_info = next((c for c in crops_data["crops"] if c["name"].lower() == crop.lower()), None)
    if not crop_info:
        raise HTTPException(status_code=404, detail=f"Crop '{crop}' not found")

    crop_prices = mandi_data.get(crop)
    if not crop_prices:
        raise HTTPException(status_code=404, detail=f"No price data for '{crop}'")

    home_data = crop_prices.get(district)
    if not home_data:
        district = list(crop_prices.keys())[0]
        home_data = crop_prices[district]

    home_price = home_data["modal_price"]

    # Build flat mandi list expected by the frontend
    all_mandis = []

    # Home mandi first
    all_mandis.append({
        "mandi_name": home_data["mandi_name"],
        "distance_km": 0,
        "modal_price": home_price,
        "transport_cost_per_quintal": 0,
        "net_price": home_price,
        "net_gain_vs_local": 0,
        "trend_7d": "+1.2%",
        "arrivals_tonnes": 230,
    })

    # Other mandis
    for mandi_district, data in crop_prices.items():
        if mandi_district == district:
            continue
        distance = data["distance_km"]
        transport = int(distance * TRANSPORT_COST_PER_KM)
        net_price = data["modal_price"] - transport
        net_gain = max(0, net_price - home_price)

        all_mandis.append({
            "mandi_name": data["mandi_name"],
            "distance_km": distance,
            "modal_price": data["modal_price"],
            "transport_cost_per_quintal": transport,
            "net_price": net_price,
            "net_gain_vs_local": net_gain,
            "trend_7d": "+0.8%",
            "arrivals_tonnes": 180,
        })

    all_mandis.sort(key=lambda x: -x["net_price"])
    best = all_mandis[0]
    best_gain = best["net_price"] - home_price

    if best_gain > 0:
        savings_en = (
            f"Sell at {best['mandi_name']} for +Rs.{best_gain}/qtl more. "
            f"After Rs.{best['transport_cost_per_quintal']}/qtl transport, you still net Rs.{best_gain}/qtl extra."
        )
        savings_hi = (
            f"{best['mandi_name']} में बेचें — Rs.{best_gain}/क्विंटल ज़्यादा मिलेगा।"
        )
    else:
        savings_en = f"Your local {all_mandis[-1]['mandi_name']} has the best net price today."
        savings_hi = f"आज आपकी स्थानीय मंडी में सबसे अच्छा भाव है।"

    return {
        "crop": crop,
        "district": district,
        "msp": crop_info["msp_2025"],
        "best_mandi": best["mandi_name"],
        "best_net_gain": max(0, best_gain),
        "savings_message_en": savings_en,
        "savings_message_hi": savings_hi,
        "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "all_mandis": all_mandis,
    }

