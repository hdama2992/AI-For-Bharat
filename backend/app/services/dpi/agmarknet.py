"""
AGMARKNET DPI Integration - Real-time Mandi Prices from data.gov.in

This module fetches live commodity prices from the Government of India's
Open Data Portal (data.gov.in) using the AGMARKNET dataset.

API Documentation: https://data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi
Resource ID: 9ef84268-d588-465a-a308-a864a43d0070
"""

from __future__ import annotations

import os
import httpx
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
from functools import lru_cache

# data.gov.in API configuration
DATA_GOV_API_BASE = "https://api.data.gov.in/resource"
AGMARKNET_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"

# Commodity name mappings (English to AGMARKNET names)
COMMODITY_MAPPINGS = {
    "soybean": ["Soyabean", "Soybean", "Soya Bean"],
    "wheat": ["Wheat", "Gehun"],
    "rice": ["Rice", "Paddy", "Paddy(Dhan)", "Paddy(Dhan)(Common)"],
    "cotton": ["Cotton", "Kapas", "Cotton (Unginned)"],
    "gram": ["Gram", "Chana", "Bengal Gram(Gram)(Whole)"],
    "mustard": ["Mustard", "Sarson", "Mustard Oil"],
    "groundnut": ["Groundnut", "Moongphali", "Groundnut pods (raw)"],
    "maize": ["Maize", "Makka", "Maize (Yellow)"],
}

# State name mappings
STATE_MAPPINGS = {
    "madhya pradesh": ["Madhya Pradesh", "MP"],
    "maharashtra": ["Maharashtra", "MH"],
    "rajasthan": ["Rajasthan", "RJ"],
    "gujarat": ["Gujarat", "GJ"],
    "uttar pradesh": ["Uttar Pradesh", "UP"],
}


class AgmarknetService:
    """Service to fetch real-time Mandi prices from data.gov.in AGMARKNET API."""
    
    def __init__(self):
        self.api_key = os.getenv("DATA_GOV_API_KEY", "")
        self.timeout = 10.0  # seconds
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 3600  # 1 hour cache
        self._last_fetch: Optional[datetime] = None
    
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)
    
    def _normalize_commodity(self, commodity: str) -> str:
        """Normalize commodity name to match API naming."""
        # Direct mappings to exact API commodity names
        direct_map = {
            "soybean": "Soyabean",
            "soya": "Soyabean",
            "wheat": "Wheat",
            "rice": "Rice",
            "paddy": "Paddy(Common)",
            "cotton": "Cotton",
            "gram": "Bengal Gram(Gram)(Whole)",
            "chana": "Bengal Gram(Gram)(Whole)",
            "mustard": "Mustard",
            "groundnut": "Groundnut",
            "maize": "Maize",
        }
        return direct_map.get(commodity.lower(), commodity)

    def _get_api_url(self, commodity: str, state: str = "", limit: int = 100) -> str:
        """Build API URL with filters."""
        base_url = f"{DATA_GOV_API_BASE}/{AGMARKNET_RESOURCE_ID}"

        # Add commodity filter with normalized name
        normalized_commodity = self._normalize_commodity(commodity)

        # Build URL - use pre-encoded filter syntax that works with data.gov.in
        url = f"{base_url}?api-key={self.api_key}&format=json&limit={limit}"
        url += f"&filters%5Bcommodity%5D={normalized_commodity}"

        # Add state filter if provided
        if state:
            url += f"&filters%5Bstate%5D={state.replace(' ', '%20')}"

        return url
    
    async def fetch_prices(
        self,
        commodity: str,
        state: str = "Madhya Pradesh",
        limit: int = 50
    ) -> Dict[str, Any]:
        """Fetch live Mandi prices for a commodity.

        First tries to fetch from specific state. If no results,
        fetches from all states to ensure we get live data.

        Returns:
            {
                "source": "data.gov.in",
                "timestamp": "2026-03-08T10:30:00",
                "commodity": "Soybean",
                "records": [...]
            }
        """
        if not self.is_configured():
            return {"error": "DATA_GOV_API_KEY not configured", "source": "none"}

        # Try with state filter first
        url = self._get_api_url(commodity, state, limit)
        result = await self._fetch_from_url(url, commodity, state)

        # If no results in preferred state, try all states
        if not result.get("records") and "error" not in result:
            url_all = self._get_api_url(commodity, "", limit)
            result = await self._fetch_from_url(url_all, commodity, "All India")

        return result

    async def _fetch_from_url(self, url: str, commodity: str, state: str) -> Dict[str, Any]:
        """Fetch from a specific URL."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                records = []
                for item in data.get("records", []):
                    records.append({
                        "market": item.get("market", ""),
                        "district": item.get("district", ""),
                        "state": item.get("state", ""),
                        "min_price": int(item.get("min_price", 0) or 0),
                        "max_price": int(item.get("max_price", 0) or 0),
                        "modal_price": int(item.get("modal_price", 0) or 0),
                        "arrival_date": item.get("arrival_date", ""),
                        "variety": item.get("variety", ""),
                    })

                return {
                    "source": "data.gov.in",
                    "timestamp": datetime.now().isoformat(),
                    "commodity": commodity,
                    "state": state,
                    "total_records": data.get("total", len(records)),
                    "records": records,
                }

        except httpx.TimeoutException:
            return {"error": "API timeout", "source": "none"}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}", "source": "none"}
        except Exception as e:
            return {"error": str(e), "source": "none"}
    
    def fetch_prices_sync(
        self, 
        commodity: str, 
        state: str = "Madhya Pradesh",
        limit: int = 50
    ) -> Dict[str, Any]:
        """Synchronous wrapper for fetch_prices."""
        return asyncio.run(self.fetch_prices(commodity, state, limit))


# Singleton instance
agmarknet_service = AgmarknetService()

