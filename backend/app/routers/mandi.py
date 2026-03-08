"""Mandi market comparison router."""

from __future__ import annotations

from fastapi import APIRouter, Query
from typing import Optional

from app.services.mandi_service import compare_mandi_prices_data, load_json

router = APIRouter(prefix="/mandi", tags=["Mandi"])


@router.get("/crops")
async def get_crops():
    data = load_json("crops.json")
    return {"crops": [item["name"] for item in data["crops"]]}


@router.get("/districts")
async def get_districts():
    data = load_json("districts.json")
    return {"districts": [item["name"] for item in data["districts"]]}


@router.get("/compare")
async def compare_mandi_prices(
    crop: str = Query(...),
    district: str = Query(...),
    household_id: Optional[str] = Query(None),
):
    result = compare_mandi_prices_data(crop=crop, district=district)
    all_mandis = result["all_mandis"]
    home = next((mandi for mandi in all_mandis if mandi["distance_km"] == 0), all_mandis[-1])
    alternatives = [mandi for mandi in all_mandis if mandi["distance_km"] != 0]

    return {
        "crop": result["crop"],
        "crop_hi": result["crop_hi"],
        "district": result["district"],
        "msp_price": result["msp_price"],
        "home_mandi": {
            "mandi_name": home["mandi_name"],
            "mandi_name_hi": home["mandi_name"],
            "district": home["district"],
            "state": home["state"],
            "modal_price": home["modal_price"],
            "min_price": None,
            "max_price": None,
            "distance_km": home["distance_km"],
            "transport_cost": home["transport_cost"],
            "net_gain": home["net_gain"],
            "last_updated": result["last_updated"],
        },
        "alternatives": [
            {
                "mandi_name": mandi["mandi_name"],
                "mandi_name_hi": mandi["mandi_name"],
                "district": mandi["district"],
                "state": mandi["state"],
                "modal_price": mandi["modal_price"],
                "min_price": None,
                "max_price": None,
                "distance_km": mandi["distance_km"],
                "transport_cost": mandi["transport_cost"],
                "net_gain": mandi["net_gain"],
                "last_updated": result["last_updated"],
            }
            for mandi in alternatives
        ],
        "best_mandi": result["best_mandi"],
        "potential_savings": result["potential_savings"],
        "recommendation": result["recommendation"],
        "recommendation_hi": result["recommendation_hi"],
    }

