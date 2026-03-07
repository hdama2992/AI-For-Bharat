"""
WhatsApp Voice-First Webhook Router
Handles incoming voice notes from Twilio WhatsApp

Flow:
1. Receive voice note from Twilio
2. Download audio and convert via Bhashini STT
3. Process with Sehat/Krishi agent
4. Generate voice response via Bhashini TTS
5. Send voice note back via Twilio
"""
import base64
import httpx
from fastapi import APIRouter, Form, Response
from twilio.rest import Client as TwilioClient
from twilio.twiml.messaging_response import MessagingResponse

from app.config import get_settings
from app.services.bhashini import bhashini_service
from app.services.agents.sehat import sehat_agent
from app.models.health import ChatMessage

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])
settings = get_settings()


def get_twilio_client():
    """Get Twilio client (lazy init)"""
    if settings.twilio_account_sid and settings.twilio_auth_token:
        return TwilioClient(settings.twilio_account_sid, settings.twilio_auth_token)
    return None


async def download_audio(media_url: str) -> bytes:
    """Download audio file from Twilio URL"""
    async with httpx.AsyncClient() as client:
        # Twilio requires auth to download media
        response = await client.get(
            media_url,
            auth=(settings.twilio_account_sid, settings.twilio_auth_token),
        )
        return response.content


async def process_voice_message(audio_bytes: bytes, from_number: str) -> str:
    """Process a voice message and return response audio URL"""
    
    # 1. Convert audio to base64 for Bhashini
    audio_b64 = base64.standard_b64encode(audio_bytes).decode("utf-8")
    
    # 2. Speech-to-Text via Bhashini (detect Hindi)
    transcribed_text = await bhashini_service.speech_to_text(
        audio_base64=audio_b64,
        source_lang="hi",  # Assume Hindi for rural users
    )
    
    if not transcribed_text:
        return "माफ कीजिए, मैं आपकी आवाज़ समझ नहीं पाया। कृपया दोबारा बोलें।"
    
    # 3. Process with Sehat Agent (health triage)
    # For prototype, route everything to health agent
    full_response = ""
    for chunk in sehat_agent.chat_stream(
        user_message=transcribed_text,
        conversation_history=[],
        household_context=None,
        language="hi",
    ):
        full_response += chunk
    
    # 4. Extract just the text response (strip triage JSON)
    response_text = full_response.split("<TRIAGE>")[0].strip()
    
    # Keep response concise for voice
    if len(response_text) > 500:
        response_text = response_text[:500] + "..."
    
    return response_text


@router.post("/webhook")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(default=""),
    NumMedia: int = Form(default=0),
    MediaUrl0: str = Form(default=None),
    MediaContentType0: str = Form(default=None),
):
    """
    Twilio WhatsApp webhook endpoint
    
    Handles:
    - Voice notes (audio/ogg, audio/mpeg)
    - Text messages (fallback)
    """
    response = MessagingResponse()
    
    try:
        # Check if this is a voice note
        if NumMedia > 0 and MediaContentType0 and "audio" in MediaContentType0:
            # Download the audio
            audio_bytes = await download_audio(MediaUrl0)
            
            # Process voice message
            response_text = await process_voice_message(audio_bytes, From)
            
            # Generate TTS response
            tts_audio_b64 = await bhashini_service.text_to_speech(
                text=response_text,
                target_lang="hi",
                gender="female",
            )
            
            if tts_audio_b64:
                # For now, send text response (TTS requires hosting audio)
                # TODO: Host audio and send media message
                msg = response.message(response_text)
            else:
                msg = response.message(response_text)
        
        elif Body:
            # Text message fallback
            # Process as text, respond with text
            full_response = ""
            for chunk in sehat_agent.chat_stream(
                user_message=Body,
                conversation_history=[],
                household_context=None,
                language="hi",
            ):
                full_response += chunk
            
            response_text = full_response.split("<TRIAGE>")[0].strip()
            if len(response_text) > 1000:
                response_text = response_text[:1000] + "..."
            
            response.message(response_text)
        
        else:
            response.message(
                "🙏 नमस्ते! मैं आशा-GPT हूं। कृपया अपना सवाल voice message में भेजें।\n"
                "Hello! I'm Asha-GPT. Please send your question as a voice message."
            )
    
    except Exception as e:
        print(f"WhatsApp webhook error: {e}")
        response.message(
            "माफ कीजिए, कुछ गड़बड़ हो गई। कृपया दोबारा कोशिश करें।\n"
            "Sorry, something went wrong. Please try again."
        )
    
    return Response(content=str(response), media_type="application/xml")

