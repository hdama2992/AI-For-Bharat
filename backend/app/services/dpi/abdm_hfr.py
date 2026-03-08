"""
ABDM Health Facility Registry (HFR) Integration Service.

This service provides:
1. Search for hospitals, PHCs, clinics, and pharmacies by location
2. Filter by specialty (gynecology, pediatrics, etc.)
3. Integration with ABDM sandbox API (when credentials available)
4. High-quality mock data fallback for hackathon demo

Reference: https://sandbox.abdm.gov.in/
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum

from app.config import get_settings

settings = get_settings()


class FacilityType(str, Enum):
    """Types of health facilities."""
    HOSPITAL = "hospital"
    PHC = "phc"  # Primary Health Centre
    PHARMACY = "pharmacy"
    CLINIC = "clinic"
    ANY = "any"


class Specialty(str, Enum):
    """Medical specialties."""
    GENERAL = "general"
    GYNECOLOGY = "gynecology"
    PEDIATRICS = "pediatrics"
    PULMONOLOGY = "pulmonology"
    CARDIOLOGY = "cardiology"
    ORTHOPEDICS = "orthopedics"
    OPHTHALMOLOGY = "ophthalmology"
    DERMATOLOGY = "dermatology"
    ANY = "any"


# Realistic mock data for Madhya Pradesh (demo-ready)
MOCK_FACILITIES = {
    "Madhya Pradesh": {
        "Harda": [
            {
                "id": "hfr_mp_harda_001",
                "name": "Harda District Hospital",
                "name_hi": "हरदा जिला अस्पताल",
                "type": FacilityType.HOSPITAL,
                "specialties": ["general", "gynecology", "pediatrics", "orthopedics"],
                "address": "Near Bus Stand, Harda, MP 461331",
                "phone": "07577-222001",
                "distance_km": 0,
                "rating": 3.8,
                "government": True,
                "emergency": True,
                "timings": "24x7",
            },
            {
                "id": "hfr_mp_harda_002",
                "name": "Community Health Center Timarni",
                "name_hi": "सामुदायिक स्वास्थ्य केंद्र टिमरनी",
                "type": FacilityType.PHC,
                "specialties": ["general", "gynecology"],
                "address": "Timarni, Harda District, MP",
                "phone": "07577-265123",
                "distance_km": 18,
                "rating": 3.5,
                "government": True,
                "emergency": False,
                "timings": "9 AM - 5 PM",
            },
            {
                "id": "hfr_mp_harda_003",
                "name": "Jan Aushadhi Kendra Harda",
                "name_hi": "जन औषधि केंद्र हरदा",
                "type": FacilityType.PHARMACY,
                "specialties": [],
                "address": "Main Market, Harda, MP 461331",
                "phone": "07577-223456",
                "distance_km": 1,
                "rating": 4.2,
                "government": True,
                "emergency": False,
                "timings": "8 AM - 9 PM",
            },
            {
                "id": "hfr_mp_harda_004",
                "name": "Dr. Sharma Clinic",
                "name_hi": "डॉ. शर्मा क्लीनिक",
                "type": FacilityType.CLINIC,
                "specialties": ["general", "pulmonology"],
                "address": "Gandhi Chowk, Harda, MP",
                "phone": "9425012345",
                "distance_km": 2,
                "rating": 4.0,
                "government": False,
                "emergency": False,
                "timings": "10 AM - 8 PM",
            },
        ],
        "Bhopal": [
            {
                "id": "hfr_mp_bhopal_001",
                "name": "AIIMS Bhopal",
                "name_hi": "एम्स भोपाल",
                "type": FacilityType.HOSPITAL,
                "specialties": ["general", "cardiology", "pulmonology", "gynecology", 
                               "pediatrics", "orthopedics", "ophthalmology"],
                "address": "Saket Nagar, Bhopal, MP 462020",
                "phone": "0755-2672355",
                "distance_km": 0,
                "rating": 4.5,
                "government": True,
                "emergency": True,
                "timings": "24x7",
            },
        ],
    }
}


class ABDMHealthFacilityService:
    """Service for searching health facilities via ABDM HFR or mock data."""
    
    def __init__(self):
        self.use_sandbox = False  # Set True when ABDM credentials available
    
    def is_configured(self) -> bool:
        """Check if ABDM sandbox is configured."""
        return self.use_sandbox and bool(getattr(settings, 'abdm_client_id', None))
    
    def search_facilities(
        self,
        state: str,
        district: str,
        facility_type: str = "any",
        specialty: str = "any",
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Search for health facilities in a given location.
        
        Args:
            state: State name (e.g., "Madhya Pradesh")
            district: District name (e.g., "Harda")
            facility_type: Type of facility (hospital, phc, pharmacy, clinic, any)
            specialty: Medical specialty to filter by
            limit: Maximum number of results
            
        Returns:
            Dict with facilities list, total count, and metadata
        """
        # TODO: Implement ABDM sandbox API when credentials available
        return self._search_mock_facilities(state, district, facility_type, specialty, limit)

    def _search_mock_facilities(
        self,
        state: str,
        district: str,
        facility_type: str,
        specialty: str,
        limit: int
    ) -> Dict[str, Any]:
        """Search mock facilities database."""
        # Get facilities for the state/district
        state_data = MOCK_FACILITIES.get(state, {})
        facilities = state_data.get(district, [])

        # If district not found, try to find nearby district
        if not facilities and state_data:
            # Fallback to first available district in state
            first_district = list(state_data.keys())[0]
            facilities = state_data.get(first_district, [])
            district = first_district

        # Filter by facility type
        if facility_type and facility_type != "any":
            facilities = [f for f in facilities if f["type"].value == facility_type]

        # Filter by specialty
        if specialty and specialty != "any":
            facilities = [f for f in facilities if specialty in f.get("specialties", [])]

        # Sort by distance
        facilities = sorted(facilities, key=lambda f: f.get("distance_km", 999))

        # Limit results
        facilities = facilities[:limit]

        return {
            "facilities": facilities,
            "total": len(facilities),
            "state": state,
            "district": district,
            "filters": {
                "facility_type": facility_type,
                "specialty": specialty
            },
            "source": "mock (ABDM sandbox pending)",
            "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }

    def format_response(
        self,
        result: Dict[str, Any],
        language: str = "en"
    ) -> str:
        """Format search results into natural language response."""
        facilities = result.get("facilities", [])

        if not facilities:
            if language == "hi":
                return "मुझे इस क्षेत्र में कोई स्वास्थ्य सुविधा नहीं मिली। कृपया जिला बदलकर देखें।"
            return "I couldn't find any health facilities in this area. Please try a different district."

        if language == "hi":
            lines = [f"मुझे {result['district']} में {len(facilities)} स्वास्थ्य सुविधाएं मिलीं:\n"]
            for i, f in enumerate(facilities, 1):
                name = f.get("name_hi", f["name"])
                govt = "🏥 सरकारी" if f.get("government") else "🏨 निजी"
                emerg = "| 🚨 आपातकालीन" if f.get("emergency") else ""
                lines.append(f"{i}. **{name}** ({govt}{emerg})")
                lines.append(f"   📍 {f['address']}")
                lines.append(f"   📞 {f['phone']} | ⏰ {f['timings']}")
                if f.get("distance_km", 0) > 0:
                    lines.append(f"   🚗 ~{f['distance_km']} km दूर")
                lines.append("")
            return "\n".join(lines)
        else:
            lines = [f"I found {len(facilities)} health facilities in {result['district']}:\n"]
            for i, f in enumerate(facilities, 1):
                govt = "🏥 Government" if f.get("government") else "🏨 Private"
                emerg = " | 🚨 Emergency" if f.get("emergency") else ""
                lines.append(f"{i}. **{f['name']}** ({govt}{emerg})")
                lines.append(f"   📍 {f['address']}")
                lines.append(f"   📞 {f['phone']} | ⏰ {f['timings']}")
                if f.get("distance_km", 0) > 0:
                    lines.append(f"   🚗 ~{f['distance_km']} km away")
                lines.append("")
            return "\n".join(lines)

    def get_emergency_facility(self, state: str, district: str) -> Optional[Dict]:
        """Quick lookup for nearest emergency facility."""
        result = self.search_facilities(state, district, "hospital", "any", 10)
        for f in result.get("facilities", []):
            if f.get("emergency"):
                return f
        return None


# Singleton instance
abdm_hfr_service = ABDMHealthFacilityService()

