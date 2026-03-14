#!/usr/bin/env python3
"""
Test Full Voice Flow: Voice Input → STT → DPI Orchestrator → TTS → Voice Output

This script simulates the complete voice-first interaction:
1. Record/use sample audio
2. STT via Sarvam 
3. Process through DPI orchestrator
4. TTS response via Sarvam
5. Play audio output

Usage:
    python test_voice_flow.py
"""
import asyncio
import base64
import os
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()


async def test_tts_only():
    """Test TTS with a sample Hindi text."""
    from app.services.speech_provider import get_speech_provider, SpeechProviderError
    
    print("=" * 60)
    print("🔊 TEST 1: Text-to-Speech (TTS)")
    print("=" * 60)
    
    provider = get_speech_provider()
    test_texts = [
        ("hi", "नमस्ते, मैं विकास-GPT हूं। मैं आपकी मदद कर सकता हूं।"),
        ("hi", "हर्दा में 3 जन औषधि केंद्र हैं। सबसे नज़दीक हर्दा बस स्टैंड पर है।"),
        ("en", "Hello, I am VikasGPT. I can help you with health, mandi prices, and more."),
    ]
    
    for lang, text in test_texts:
        print(f"\n📝 Input ({lang}): {text[:50]}...")
        try:
            audio_b64 = await provider.text_to_speech(text, target_lang=lang)
            audio_bytes = base64.b64decode(audio_b64)
            print(f"✅ TTS Success! Audio size: {len(audio_bytes)} bytes")
            
            # Save to file for playback
            filename = f"test_output_{lang}.wav"
            with open(filename, "wb") as f:
                f.write(audio_bytes)
            print(f"   Saved to: {filename}")
            
        except SpeechProviderError as e:
            print(f"❌ TTS Error: {e}")


async def test_full_dpi_flow():
    """Test DPI orchestrator with voice response generation."""
    from app.services.dpi import slot_filling_orchestrator, jan_aushadhi_service
    from app.services.speech_provider import get_speech_provider, SpeechProviderError
    
    print("\n" + "=" * 60)
    print("🔄 TEST 2: Full DPI Flow (Query → Slot-Fill → API → TTS)")
    print("=" * 60)
    
    provider = get_speech_provider()
    
    # Simulate user context from onboarding
    context = {
        "state": "Madhya Pradesh",
        "district": "Harda",
        "crop_primary": "Soybean",
        "name": "Rajesh"
    }
    
    queries = [
        ("hi", "जन औषधि केंद्र कहाँ है?"),
        ("hi", "मंडी तक माल पहुंचाने में कितना खर्चा आएगा?"),
        ("en", "Where is the nearest hospital?"),
    ]
    
    for lang, query in queries:
        print(f"\n🎤 User Query ({lang}): {query}")
        
        # Step 1: DPI Orchestrator
        result = slot_filling_orchestrator.process_turn(
            user_message=query,
            current_slots={},
            household_context=context,
            language=lang,
        )
        
        print(f"   Service: {result.get('service')}")
        print(f"   Ready for API: {result.get('ready_for_api')}")
        
        # Step 2: Get response text
        if result.get("ready_for_api") and result.get("service"):
            service = result["service"]
            api_params = result.get("api_params", {})
            
            # Call the appropriate service
            if "JAN_AUSHADHI" in str(service):
                api_result = jan_aushadhi_service.search_kendras(
                    district=api_params.get("district", "Harda"),
                    state=api_params.get("state", "Madhya Pradesh"),
                )
                response_text = api_result.get(f"response_text_{lang}", api_result.get("response_text_hi", "")) or "जानकारी मिल गई।"
            else:
                response_text = result.get("clarifying_question") or "मैं इस सेवा के लिए जानकारी खोज रहा हूं।"
        else:
            response_text = result.get("clarifying_question") or "कृपया अधिक जानकारी दें।"
        
        print(f"   Response: {response_text[:80]}...")
        
        # Step 3: TTS
        try:
            audio_b64 = await provider.text_to_speech(response_text, target_lang=lang)
            audio_bytes = base64.b64decode(audio_b64)
            print(f"   ✅ TTS: {len(audio_bytes)} bytes")
        except SpeechProviderError as e:
            print(f"   ❌ TTS Error: {e}")


async def test_api_endpoints():
    """Test the REST API endpoints."""
    import httpx
    
    print("\n" + "=" * 60)
    print("🌐 TEST 3: REST API Endpoints")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api/v1"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test TTS endpoint
        print("\n📡 POST /voice/tts")
        try:
            response = await client.post(
                f"{base_url}/voice/tts",
                json={"text": "नमस्ते, यह एक परीक्षण है।", "target_language": "hi"}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: {response.status_code}, Audio length: {len(data.get('audio_base64', ''))}")
            else:
                print(f"   ❌ Status: {response.status_code}, Error: {response.text[:100]}")
        except Exception as e:
            print(f"   ⚠️ Server not running? Error: {e}")
        
        # Test Chat endpoint
        print("\n📡 POST /chat/turn")
        try:
            response = await client.post(
                f"{base_url}/chat/turn",
                json={"session_id": "test-voice-flow", "message": "जन औषधि केंद्र कहाँ है?", "language": "hi"}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: {response.status_code}")
                print(f"   Reply: {data.get('reply', '')[:80]}...")
            else:
                print(f"   ❌ Status: {response.status_code}, Error: {response.text[:100]}")
        except Exception as e:
            print(f"   ⚠️ Server not running? Error: {e}")


async def main():
    print("🎤 VikasGPT Voice Flow Test")
    print("=" * 60)
    
    # Test 1: TTS only (no server needed)
    await test_tts_only()
    
    # Test 2: Full DPI flow (no server needed)
    await test_full_dpi_flow()
    
    # Test 3: API endpoints (server must be running)
    await test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("✅ All voice flow tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

