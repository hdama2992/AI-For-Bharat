"""
Transport/Logistics Service (Dhwani Agent) - Rural goods transport estimation.

For farmers to transport crops from farm to mandi or other destinations.
Real integration would use ONDC Logistics network, but for prototype using
distance-based cost estimation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class VehicleType(str, Enum):
    TRACTOR = "tractor"
    PICKUP = "pickup"
    MINI_TRUCK = "mini_truck"
    TRUCK = "truck"


@dataclass
class TransportOption:
    """A transport option with vehicle and pricing."""
    vehicle_type: VehicleType
    vehicle_name_hi: str
    vehicle_name_en: str
    capacity_quintals: float
    base_rate_per_km: float  # INR per km
    loading_charge: float  # INR flat


# Transport options available in rural MP
TRANSPORT_OPTIONS: List[TransportOption] = [
    TransportOption(
        vehicle_type=VehicleType.TRACTOR,
        vehicle_name_hi="ट्रैक्टर ट्रॉली",
        vehicle_name_en="Tractor Trolley",
        capacity_quintals=30,
        base_rate_per_km=15,
        loading_charge=200,
    ),
    TransportOption(
        vehicle_type=VehicleType.PICKUP,
        vehicle_name_hi="पिकअप",
        vehicle_name_en="Pickup Van",
        capacity_quintals=10,
        base_rate_per_km=12,
        loading_charge=150,
    ),
    TransportOption(
        vehicle_type=VehicleType.MINI_TRUCK,
        vehicle_name_hi="छोटा टेम्पो",
        vehicle_name_en="Mini Truck",
        capacity_quintals=20,
        base_rate_per_km=18,
        loading_charge=300,
    ),
    TransportOption(
        vehicle_type=VehicleType.TRUCK,
        vehicle_name_hi="ट्रक",
        vehicle_name_en="Truck",
        capacity_quintals=100,
        base_rate_per_km=25,
        loading_charge=500,
    ),
]

# Approximate distances from Harda to nearby mandis (km)
MANDI_DISTANCES: Dict[str, float] = {
    "harda": 0,
    "timarni": 25,
    "hoshangabad": 65,
    "betul": 90,
    "itarsi": 45,
    "bhopal": 150,
    "indore": 200,
}


class TransportService:
    """Service for estimating transport costs to mandis."""

    def __init__(self):
        self.options = TRANSPORT_OPTIONS
        self.distances = MANDI_DISTANCES

    def estimate_transport(
        self,
        from_location: str,
        to_mandi: str,
        quantity_quintals: float,
        preferred_vehicle: Optional[VehicleType] = None,
    ) -> Dict[str, Any]:
        """
        Estimate transport cost for moving goods to mandi.

        Args:
            from_location: Origin (usually farmer's village/district)
            to_mandi: Destination mandi name
            quantity_quintals: Quantity in quintals
            preferred_vehicle: Optional preferred vehicle type

        Returns:
            Dict with transport options and estimated costs
        """
        # Get distance (use default if not found)
        to_mandi_lower = to_mandi.lower()
        distance_km = self.distances.get(to_mandi_lower, 50)  # Default 50km

        # Calculate costs for each suitable vehicle
        estimates = []
        for option in self.options:
            if option.capacity_quintals >= quantity_quintals:
                trips = 1
            else:
                trips = int(quantity_quintals / option.capacity_quintals) + 1

            total_cost = (
                (distance_km * option.base_rate_per_km * trips) +
                (option.loading_charge * trips)
            )

            estimates.append({
                "vehicle_type": option.vehicle_type.value,
                "vehicle_name_hi": option.vehicle_name_hi,
                "vehicle_name_en": option.vehicle_name_en,
                "capacity_quintals": option.capacity_quintals,
                "trips_required": trips,
                "distance_km": distance_km,
                "estimated_cost": round(total_cost),
                "cost_per_quintal": round(total_cost / quantity_quintals),
            })

        # Sort by cost
        estimates.sort(key=lambda x: x["estimated_cost"])

        # Format bilingual response
        best = estimates[0] if estimates else None
        response_hi = self._format_response_hindi(best, to_mandi, quantity_quintals, distance_km)
        response_en = self._format_response_english(best, to_mandi, quantity_quintals, distance_km)

        return {
            "success": True,
            "from_location": from_location,
            "to_mandi": to_mandi,
            "distance_km": distance_km,
            "quantity_quintals": quantity_quintals,
            "estimates": estimates,
            "recommended": best,
            "response_text_hi": response_hi,
            "response_text_en": response_en,
        }

    def _format_response_hindi(self, best: Dict, mandi: str, qty: float, dist: float) -> str:
        """Format response in Hindi for TTS."""
        if not best:
            return "माफ़ कीजिए, ट्रांसपोर्ट का अनुमान नहीं लगा सके।"
        return (
            f"{mandi} मंडी {dist} किलोमीटर दूर है। "
            f"{qty} क्विंटल माल ले जाने के लिए {best['vehicle_name_hi']} से "
            f"लगभग {best['estimated_cost']} रुपये लगेंगे। "
            f"प्रति क्विंटल {best['cost_per_quintal']} रुपये का खर्चा आएगा।"
        )

    def _format_response_english(self, best: Dict, mandi: str, qty: float, dist: float) -> str:
        """Format response in English."""
        if not best:
            return "Sorry, could not estimate transport cost."
        return (
            f"{mandi} mandi is {dist} km away. "
            f"To transport {qty} quintals using {best['vehicle_name_en']}, "
            f"it will cost approximately ₹{best['estimated_cost']}. "
            f"That's ₹{best['cost_per_quintal']} per quintal."
        )


# Singleton instance
transport_service = TransportService()

