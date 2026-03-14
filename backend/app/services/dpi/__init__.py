# DPI (Digital Public Infrastructure) integrations
"""
India DPI Integration Layer for VikasGPT

Integrated DPIs:
- AGMARKNET (data.gov.in): Real-time Mandi prices for agricultural commodities
- ABDM HFR: Health Facility Registry for hospitals, PHCs, pharmacies
- Jan Aushadhi: Generic medicine stores (50-90% cheaper medicines)
- Transport (Dhwani): Goods transport cost estimation to mandis

AI Orchestration:
- slot_filling_orchestrator: Evidence-First Slot-Filling for DPI queries
- dpi_orchestrator: Basic intent classification and parameter extraction
"""

from .agmarknet import agmarknet_service
from .abdm_hfr import abdm_hfr_service
from .jan_aushadhi import jan_aushadhi_service
from .transport import transport_service
from .ai_orchestrator import dpi_orchestrator, slot_filling_orchestrator, DPIService

__all__ = [
    "agmarknet_service",
    "abdm_hfr_service",
    "jan_aushadhi_service",
    "transport_service",
    "dpi_orchestrator",
    "slot_filling_orchestrator",
    "DPIService",
]

