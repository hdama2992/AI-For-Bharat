"""
Jan Aushadhi Kendra (JAK) Service - Generic medicine store locator.

Jan Aushadhi Kendras sell generic medicines at 50-90% lower prices than branded medicines.
This service helps farmers find nearby Jan Aushadhi stores.

Data source: data.gov.in (District-wise Jan Aushadhi Kendras datasets)
For prototype: Using realistic mock data for MP region
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class JanAushadhiKendra:
    """Represents a Jan Aushadhi Kendra (generic medicine store)."""
    store_id: str
    name: str
    address: str
    district: str
    state: str
    pincode: str
    contact_number: str
    timings: str
    distance_km: Optional[float] = None


# Realistic mock data for Madhya Pradesh districts
MOCK_JAN_AUSHADHI_KENDRAS: List[Dict[str, Any]] = [
    # Harda District
    {
        "store_id": "JAK-MP-HDR-001",
        "name": "Jan Aushadhi Kendra - Harda",
        "address": "Near Civil Hospital, Main Road, Harda",
        "district": "Harda",
        "state": "Madhya Pradesh",
        "pincode": "461331",
        "contact_number": "07577-225100",
        "timings": "8:00 AM - 8:00 PM",
    },
    {
        "store_id": "JAK-MP-HDR-002",
        "name": "Jan Aushadhi Kendra - Timarni",
        "address": "Bus Stand Road, Timarni, Harda",
        "district": "Harda",
        "state": "Madhya Pradesh",
        "pincode": "461228",
        "contact_number": "07577-252200",
        "timings": "9:00 AM - 7:00 PM",
    },
    # Hoshangabad District (nearby)
    {
        "store_id": "JAK-MP-HSB-001",
        "name": "Jan Aushadhi Kendra - Hoshangabad",
        "address": "Civil Lines, Near District Hospital, Hoshangabad",
        "district": "Hoshangabad",
        "state": "Madhya Pradesh",
        "pincode": "461001",
        "contact_number": "07574-253300",
        "timings": "8:00 AM - 9:00 PM",
    },
    # Betul District (nearby)
    {
        "store_id": "JAK-MP-BTL-001",
        "name": "Jan Aushadhi Kendra - Betul",
        "address": "Near Bus Stand, Betul",
        "district": "Betul",
        "state": "Madhya Pradesh",
        "pincode": "460001",
        "contact_number": "07141-234500",
        "timings": "8:30 AM - 8:00 PM",
    },
    # Bhopal (state capital - reference)
    {
        "store_id": "JAK-MP-BPL-001",
        "name": "Jan Aushadhi Kendra - Hamidia Hospital",
        "address": "Hamidia Hospital Complex, Bhopal",
        "district": "Bhopal",
        "state": "Madhya Pradesh",
        "pincode": "462001",
        "contact_number": "0755-2540100",
        "timings": "24 Hours",
    },
]


class JanAushadhiService:
    """Service for finding Jan Aushadhi Kendras (generic medicine stores)."""

    def __init__(self):
        self.kendras = MOCK_JAN_AUSHADHI_KENDRAS

    def search_kendras(
        self,
        district: str,
        state: str = "Madhya Pradesh",
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Search for Jan Aushadhi Kendras near a district.

        Args:
            district: District name
            state: State name (default: MP)
            limit: Max results

        Returns:
            Dict with kendras list and formatted response
        """
        district_lower = district.lower()
        state_lower = state.lower()

        # Find exact matches first, then nearby districts
        exact_matches = []
        nearby_matches = []

        for kendra in self.kendras:
            if kendra["district"].lower() == district_lower:
                exact_matches.append(kendra)
            elif kendra["state"].lower() == state_lower:
                nearby_matches.append(kendra)

        results = (exact_matches + nearby_matches)[:limit]

        if not results:
            return {
                "success": False,
                "kendras": [],
                "message": f"No Jan Aushadhi Kendras found near {district}",
                "response_text_hi": f"माफ़ कीजिए, {district} के पास कोई जन औषधि केंद्र नहीं मिला।",
                "response_text_en": f"Sorry, no Jan Aushadhi Kendra found near {district}.",
            }

        # Format bilingual response for TTS
        response_hi = self._format_response_hindi(results, district)
        response_en = self._format_response_english(results, district)

        return {
            "success": True,
            "kendras": results,
            "count": len(results),
            "response_text_hi": response_hi,
            "response_text_en": response_en,
        }

    def _format_response_hindi(self, kendras: List[Dict], district: str) -> str:
        """Format response in Hindi for TTS."""
        if len(kendras) == 1:
            k = kendras[0]
            return (
                f"{district} में एक जन औषधि केंद्र है। "
                f"{k['name']}, पता: {k['address']}। "
                f"फ़ोन नंबर: {k['contact_number']}। "
                f"समय: {k['timings']}। "
                f"यहाँ दवाइयाँ 50 से 90 प्रतिशत सस्ती मिलती हैं।"
            )
        return (
            f"{district} के पास {len(kendras)} जन औषधि केंद्र हैं। "
            f"सबसे नज़दीकी है {kendras[0]['name']}, {kendras[0]['address']}। "
            f"फ़ोन: {kendras[0]['contact_number']}। "
            f"जन औषधि में जेनेरिक दवाइयाँ बहुत सस्ती मिलती हैं।"
        )

    def _format_response_english(self, kendras: List[Dict], district: str) -> str:
        """Format response in English."""
        if len(kendras) == 1:
            k = kendras[0]
            return (
                f"There is 1 Jan Aushadhi Kendra in {district}. "
                f"{k['name']} at {k['address']}. "
                f"Phone: {k['contact_number']}. Timings: {k['timings']}. "
                f"Medicines here are 50-90% cheaper than branded ones."
            )
        return (
            f"Found {len(kendras)} Jan Aushadhi Kendras near {district}. "
            f"Nearest: {kendras[0]['name']} at {kendras[0]['address']}. "
            f"Phone: {kendras[0]['contact_number']}. "
            f"Generic medicines at Jan Aushadhi are very affordable."
        )


# Singleton instance
jan_aushadhi_service = JanAushadhiService()

