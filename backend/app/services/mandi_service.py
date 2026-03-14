"""Shared mandi compare logic and lightweight query extraction.

Integrates with data.gov.in AGMARKNET API for real-time prices,
with fallback to local mock data when API is unavailable.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import re
from typing import Any, Dict, Optional
import asyncio

from fastapi import HTTPException

from app.config import get_settings
from app.services.agents.prompts import MANDI_ADVISOR_PROMPT, MANDI_EXTRACTION_PROMPT
from app.services.bedrock import bedrock_service
from app.services.dpi.agmarknet import agmarknet_service

settings = get_settings()
DATA_DIR = Path(__file__).parent.parent.parent / "data"
TRANSPORT_COST_PER_KM = 3.0


def load_json(filename: str) -> dict:
    with open(DATA_DIR / filename, encoding="utf-8") as handle:
        return json.load(handle)


async def fetch_live_prices(crop: str, state: str = "Madhya Pradesh") -> Optional[Dict[str, Any]]:
    """Fetch live prices from data.gov.in AGMARKNET API."""
    if not agmarknet_service.is_configured():
        return None

    try:
        result = await agmarknet_service.fetch_prices(crop, state, limit=20)
        if "error" not in result and result.get("records"):
            return result
    except Exception as exc:
        print(f"Live price fetch failed: {exc}")
    return None


def _build_result_from_live_data(
    live_data: Dict[str, Any],
    crop_info: Dict[str, Any],
    district: str
) -> Optional[Dict[str, Any]]:
    """Build result from live AGMARKNET data."""
    records = live_data.get("records", [])
    if not records:
        return None

    # Group by market and find best prices
    all_mandis = []
    home_price = None

    for record in records:
        market_name = record.get("market", "")
        rec_district = record.get("district", "")
        modal_price = record.get("modal_price", 0)

        if not modal_price:
            continue

        # Check if this is the home district
        is_home = rec_district.lower() == district.lower()
        distance_km = 0 if is_home else 50  # Estimate distance for live data

        if is_home and home_price is None:
            home_price = modal_price

        transport = int(distance_km * TRANSPORT_COST_PER_KM)
        net_price = modal_price - transport

        all_mandis.append({
            "mandi_name": f"{market_name} Mandi",
            "distance_km": distance_km,
            "modal_price": modal_price,
            "min_price": record.get("min_price", modal_price),
            "max_price": record.get("max_price", modal_price),
            "transport_cost": transport,
            "net_price": net_price,
            "net_gain": 0,  # Will calculate after sorting
            "district": rec_district,
            "state": record.get("state", ""),
            "arrival_date": record.get("arrival_date", ""),
            "source": "data.gov.in",
        })

    if not all_mandis:
        return None

    # Use first record's price if home not found
    if home_price is None:
        home_price = all_mandis[0]["modal_price"]

    # Calculate net gains and sort
    for mandi in all_mandis:
        mandi["net_gain"] = max(0, mandi["net_price"] - home_price)

    all_mandis.sort(key=lambda m: m["net_price"], reverse=True)
    best = all_mandis[0]
    gain = max(0, best["net_price"] - home_price)

    recommendation = (
        f"🌐 LIVE: Sell at {best['mandi_name']} for about ₹{gain}/qtl extra."
        if gain > 0
        else f"🌐 LIVE: Your local mandi in {district} has the best price today."
    )
    recommendation_hi = (
        f"🌐 लाइव: {best['mandi_name']} में बेचने पर लगभग ₹{gain}/क्विंटल अधिक मिलेगा।"
        if gain > 0
        else f"🌐 लाइव: आज {district} की मंडी में सबसे अच्छा भाव है।"
    )

    return {
        "crop": crop_info["name"],
        "crop_hi": crop_info.get("name_hi", crop_info["name"]),
        "district": district,
        "msp_price": crop_info["msp_2025"],
        "best_mandi": best["mandi_name"],
        "potential_savings": gain,
        "recommendation": recommendation,
        "recommendation_hi": recommendation_hi,
        "all_mandis": all_mandis,
        "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "data_source": "data.gov.in (AGMARKNET)",
    }


def compare_mandi_prices_data(crop: str, district: str, use_live: bool = True) -> Dict[str, Any]:
    """Compare Mandi prices, using live data.gov.in API first with fallback to mock."""
    crops_data = load_json("crops.json")
    crop_info = next((item for item in crops_data["crops"] if item["name"].lower() == crop.lower()), None)
    if not crop_info:
        raise HTTPException(status_code=404, detail=f"Crop '{crop}' not found")

    # Try live data first
    if use_live and agmarknet_service.is_configured():
        try:
            live_data = asyncio.run(fetch_live_prices(crop, "Madhya Pradesh"))
            if live_data:
                result = _build_result_from_live_data(live_data, crop_info, district)
                if result:
                    print(f"✅ Using LIVE data from data.gov.in for {crop}")
                    return result
        except Exception as exc:
            print(f"⚠️ Live data fetch failed: {exc}, falling back to mock")

    # Fallback to mock data
    print(f"📁 Using MOCK data for {crop}")
    mandi_data = load_json("mandi_prices.json")
    crop_prices = mandi_data.get(crop)
    if not crop_prices:
        raise HTTPException(status_code=404, detail=f"No price data for '{crop}'")

    home_data = crop_prices.get(district)
    if not home_data:
        district = list(crop_prices.keys())[0]
        home_data = crop_prices[district]

    home_price = home_data["modal_price"]
    all_mandis = [{
        "mandi_name": home_data["mandi_name"],
        "distance_km": 0,
        "modal_price": home_price,
        "transport_cost": 0,
        "net_price": home_price,
        "net_gain": 0,
        "district": district,
        "state": home_data["state"],
        "source": "mock",
    }]

    for mandi_district, item in crop_prices.items():
        if mandi_district == district:
            continue
        transport = int(item["distance_km"] * TRANSPORT_COST_PER_KM)
        net_price = item["modal_price"] - transport
        all_mandis.append({
            "mandi_name": item["mandi_name"],
            "distance_km": item["distance_km"],
            "modal_price": item["modal_price"],
            "transport_cost": transport,
            "net_price": net_price,
            "net_gain": max(0, net_price - home_price),
            "district": mandi_district,
            "state": item["state"],
            "source": "mock",
        })

    all_mandis.sort(key=lambda mandi: mandi["net_price"], reverse=True)
    best = all_mandis[0]
    gain = max(0, best["net_price"] - home_price)

    recommendation = (
        f"Sell at {best['mandi_name']} for about ₹{gain}/qtl extra after transport."
        if gain > 0
        else f"Your local mandi in {district} is the best net price today."
    )
    recommendation_hi = (
        f"{best['mandi_name']} में बेचने पर परिवहन के बाद लगभग ₹{gain}/क्विंटल अधिक मिल सकता है।"
        if gain > 0
        else f"आज {district} की आपकी स्थानीय मंडी में सबसे अच्छा शुद्ध भाव है।"
    )

    return {
        "crop": crop_info["name"],
        "crop_hi": crop_info.get("name_hi", crop_info["name"]),
        "district": district,
        "msp_price": crop_info["msp_2025"],
        "best_mandi": best["mandi_name"],
        "potential_savings": gain,
        "recommendation": recommendation,
        "recommendation_hi": recommendation_hi,
        "all_mandis": all_mandis,
        "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "data_source": "mock (offline)",
    }


def _fallback_extract(message: str) -> Dict[str, Any]:
    data = load_json("crops.json")
    districts = load_json("districts.json")
    crop = next((item["name"] for item in data["crops"] if item["name"].lower() in message.lower()), None)
    district = next((item["name"] for item in districts["districts"] if item["name"].lower() in message.lower()), None)
    quantity_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:quintal|quintals|qtl|qtl\.|क्विंटल)", message.lower())
    return {
        "crop": crop,
        "district": district,
        "quantity_quintal": float(quantity_match.group(1)) if quantity_match else None,
        "needs_comparison": True,
        "confidence": 0.55 if crop or district else 0.2,
    }


class MandiService:
    def extract_query(self, message: str) -> Dict[str, Any]:
        if bedrock_service.is_configured():
            try:
                response = bedrock_service.invoke_haiku(
                    [{"role": "user", "content": message}],
                    system_prompt=MANDI_EXTRACTION_PROMPT,
                ).strip()
                cleaned = response.strip("`")
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict):
                    return parsed
            except Exception as exc:
                print(f"Mandi extraction fallback triggered: {exc}")
        return _fallback_extract(message)

    def explain_result(self, result: Dict[str, Any], language: str = "en") -> str:
        top = result["all_mandis"][0]
        local = next((mandi for mandi in result["all_mandis"] if mandi["distance_km"] == 0), top)
        if language == "hi":
            return (
                f"सबसे अच्छा शुद्ध भाव {top['mandi_name']} में है। स्थानीय मंडी {local['mandi_name']} की तुलना में "
                f"लगभग ₹{result['potential_savings']}/क्विंटल अधिक मिल सकता है।"
            )
        return (
            f"The best net price is at {top['mandi_name']}. Compared with your local mandi {local['mandi_name']}, "
            f"you can make about ₹{result['potential_savings']}/qtl extra."
        )


mandi_service = MandiService()

