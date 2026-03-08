#!/usr/bin/env python3
"""Test the DPI Orchestrator and Slot-Filling logic."""

from dotenv import load_dotenv
load_dotenv()

from app.services.dpi import dpi_orchestrator, slot_filling_orchestrator, abdm_hfr_service

# Test with household context (simulating onboarded farmer Rajesh)
household_context = {
    'name': 'Rajesh',
    'state': 'Madhya Pradesh',
    'district': 'Harda',
    'crop_primary': 'Soybean',
    'family_members': [{'name': 'Sunita', 'relation': 'wife'}]
}

def test_ai_orchestrator():
    """Test basic intent classification."""
    print('=' * 60)
    print('TEST 1: AI Orchestrator Classification')
    print('=' * 60)
    
    # Test mandi query in Hindi
    result1 = dpi_orchestrator.classify_and_extract(
        'soybean ka bhav kya hai?',
        household_context
    )
    print(f'Query: "soybean ka bhav kya hai?"')
    print(f'Service: {result1.get("service")}')
    print(f'Confidence: {result1.get("confidence")}')
    print(f'Parameters: {result1.get("parameters")}')
    print()
    
    # Test health facility query
    result2 = dpi_orchestrator.classify_and_extract(
        'nearest hospital batao',
        household_context
    )
    print(f'Query: "nearest hospital batao"')
    print(f'Service: {result2.get("service")}')
    print(f'Parameters: {result2.get("parameters")}')
    print()
    
    # Test pharmacy query
    result3 = dpi_orchestrator.classify_and_extract(
        'dawai ki dukan kahan hai',
        household_context
    )
    print(f'Query: "dawai ki dukan kahan hai"')
    print(f'Service: {result3.get("service")}')
    print(f'Parameters: {result3.get("parameters")}')
    print()


def test_slot_filling():
    """Test Evidence-First Slot-Filling."""
    print('=' * 60)
    print('TEST 2: Evidence-First Slot-Filling')
    print('=' * 60)
    
    # User asks about mandi prices without specifying crop
    # But household context has crop_primary = Soybean
    result = slot_filling_orchestrator.process_turn(
        user_message="mandi mein aaj bhav kaisa hai?",
        current_slots={},
        household_context=household_context,
        language="en"
    )
    
    print(f'Query: "mandi mein aaj bhav kaisa hai?"')
    print(f'Service: {result["service"]}')
    print(f'Slots: {result["slots"]}')
    print(f'Slots Complete: {result["slots_complete"]}')
    print(f'Missing Slots: {result["missing_slots"]}')
    print(f'Clarifying Question: {result["clarifying_question"]}')
    print(f'Ready for API: {result["ready_for_api"]}')
    if result["ready_for_api"]:
        print(f'API Params: {result["api_params"]}')
    print()


def test_health_facility_search():
    """Test ABDM HFR mock search."""
    print('=' * 60)
    print('TEST 3: Health Facility Search (ABDM HFR)')
    print('=' * 60)
    
    # Search for hospitals in Harda
    result = abdm_hfr_service.search_facilities(
        state="Madhya Pradesh",
        district="Harda",
        facility_type="hospital",
        specialty="any"
    )
    
    print(f'Search: Hospitals in Harda, MP')
    print(f'Found: {result["total"]} facilities')
    print(f'Source: {result["source"]}')
    print()
    
    for facility in result["facilities"]:
        print(f'  - {facility["name"]}')
        print(f'    Type: {facility["type"].value}')
        print(f'    Govt: {facility["government"]}')
        print(f'    Emergency: {facility["emergency"]}')
        print(f'    Phone: {facility["phone"]}')
        print()
    
    # Format response for TTS
    print('Formatted Response (English):')
    print('-' * 40)
    print(abdm_hfr_service.format_response(result, "en"))
    print()
    
    print('Formatted Response (Hindi):')
    print('-' * 40)
    print(abdm_hfr_service.format_response(result, "hi"))


if __name__ == "__main__":
    test_ai_orchestrator()
    test_slot_filling()
    test_health_facility_search()
    print('=' * 60)
    print('ALL TESTS COMPLETED!')
    print('=' * 60)

