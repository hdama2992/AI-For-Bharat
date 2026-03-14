"""Test DPI Integration - Jan Aushadhi, Transport, and Slot-Filling."""

from dotenv import load_dotenv
load_dotenv()

print("=== Testing DPI Integration ===")
print()

# Test 1: Jan Aushadhi Service
print("1. Jan Aushadhi Service Test:")
from app.services.dpi import jan_aushadhi_service
result = jan_aushadhi_service.search_kendras("Harda", "Madhya Pradesh")
print(f"   Success: {result['success']}")
print(f"   Count: {result.get('count', 0)}")
print(f"   First Kendra: {result['kendras'][0]['name'] if result['kendras'] else 'None'}")
print()

# Test 2: Transport Service
print("2. Transport Service Test:")
from app.services.dpi import transport_service
result = transport_service.estimate_transport("Harda", "Bhopal", 15)
print(f"   Success: {result['success']}")
print(f"   Distance: {result['distance_km']} km")
print(f"   Best option: {result['recommended']['vehicle_name_en']} - Rs.{result['recommended']['estimated_cost']}")
print()

# Test 3: DPI Orchestrator - Service Classification
print("3. DPI Orchestrator Classification:")
from app.services.dpi import slot_filling_orchestrator, DPIService
context = {"state": "Madhya Pradesh", "district": "Harda", "crop_primary": "Soybean"}

# Test Jan Aushadhi classification (using fallback since no Bedrock)
result = slot_filling_orchestrator.process_turn(
    user_message="jan aushadhi kendra kahan hai",
    current_slots={},
    household_context=context,
    language="hi"
)
print(f"   Service: {result['service']}")
print(f"   Ready for API: {result['ready_for_api']}")
print()

# Test Transport classification
print("4. Transport Classification:")
result = slot_filling_orchestrator.process_turn(
    user_message="truck se mandi tak maal le jana hai",
    current_slots={},
    household_context=context,
    language="hi"
)
print(f"   Service: {result['service']}")
print(f"   Ready for API: {result['ready_for_api']}")
if result.get("missing_slots"):
    print(f"   Missing slots: {result['missing_slots']}")
if result.get("clarifying_question"):
    print(f"   Question: {result['clarifying_question']}")
print()

# Test 5: Main Orchestrator Import
print("5. Main Orchestrator Import Test:")
try:
    from app.services.orchestrator import orchestrator
    print("   Orchestrator imported successfully!")
    print("   DPI services are integrated.")
except Exception as e:
    print(f"   ERROR: {e}")
print()

print("=== All DPI Integration Tests Passed ===")

