"""Test script for DPI integrations."""
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from app.services.dpi.agmarknet import agmarknet_service

async def test_agmarknet():
    print("=" * 50)
    print("AGMARKNET DPI Integration Test")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv("DATA_GOV_API_KEY", "")
    print(f"\n1. API Key configured: {bool(api_key)} (length: {len(api_key)})")
    
    if not api_key:
        print("   ERROR: DATA_GOV_API_KEY not set in .env")
        return
    
    # Test fetching Soybean prices
    print("\n2. Fetching LIVE Soybean prices from data.gov.in...")
    result = await agmarknet_service.fetch_prices("Soybean", "Madhya Pradesh", limit=10)
    
    if "error" in result:
        print(f"   ERROR: {result['error']}")
        return
    
    print(f"   Source: {result.get('source')}")
    print(f"   Total records: {result.get('total_records', 0)}")
    print(f"   Timestamp: {result.get('timestamp')}")
    
    records = result.get("records", [])
    if records:
        print(f"\n3. Sample Markets ({len(records)} shown):")
        for r in records[:5]:
            market = r.get("market", "Unknown")
            district = r.get("district", "Unknown")
            price = r.get("modal_price", 0)
            print(f"   - {market} ({district}): Rs.{price}/qtl")
    else:
        print("\n   No records returned")
    
    print("\n" + "=" * 50)
    print("Test Complete!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_agmarknet())

