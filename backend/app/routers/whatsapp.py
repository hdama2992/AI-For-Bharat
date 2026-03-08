"""
WhatsApp webhook and temporary media hosting for the prototype.
"""
from __future__ import annotations
import base64
import binascii
from xml.sax.saxutils import escape

import httpx
from fastapi import APIRouter, Form, HTTPException, Request, Response
from twilio.request_validator import RequestValidator

from app.config import get_settings
from app.db.repository import repository
from app.models.chat import AgentType
from app.models.health import ChatMessage
from app.services.speech_provider import SpeechProviderError, speech_provider
from app.services.orchestrator import orchestrator

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])
settings = get_settings()


async def download_audio(media_url: str) -> bytes:
    """Download incoming WhatsApp audio from Twilio media storage."""
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        raise RuntimeError("Twilio credentials are required to download voice notes.")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            media_url,
            auth=(settings.twilio_account_sid, settings.twilio_auth_token),
        )
        response.raise_for_status()
        return response.content


def _build_media_url(media_id: str) -> str:
    base = settings.public_base_url.rstrip("/")
    return f"{base}/api/v1/whatsapp/media/{media_id}"


def _build_status_callback_url() -> str:
    base = settings.public_base_url.rstrip("/")
    return f"{base}/api/v1/whatsapp/status-callback"


def _voice_retry_message() -> str:
    return (
        "I could not understand that voice note clearly. Please send a shorter voice note or type your health problem.\n\n"
        "मैं उस वॉइस नोट को साफ़ समझ नहीं पाया। कृपया छोटा voice note भेजें या अपनी तकलीफ़ टाइप करें।"
    )


async def _transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe using the configured provider."""
    try:
        transcript = await speech_provider.speech_to_text(
            audio_bytes=audio_bytes,
            source_lang="hi",
        )
    except SpeechProviderError as exc:
        print(f"Speech-to-text failed: {exc}")
        return ""

    if not transcript:
        return ""
    return transcript.strip()


async def _create_voice_reply_url(text: str) -> str | None:
    try:
        audio_b64 = await speech_provider.text_to_speech(
            text=text,
            target_lang="hi",
            gender="female",
        )
    except SpeechProviderError as exc:
        print(f"Text-to-speech failed: {exc}")
        return None

    if not audio_b64:
        return None

    if audio_b64.startswith("data:"):
        _, _, audio_b64 = audio_b64.partition(",")

    try:
        audio_bytes = base64.b64decode(audio_b64)
    except (binascii.Error, ValueError):
        return None

    media_ref = repository.store_whatsapp_media(audio_bytes, "audio/wav", ttl_seconds=settings.s3_media_ttl_seconds)
    return _build_media_url(media_ref.media_id)


def _build_whatsapp_response(reply_text: str, media_url: str | None = None) -> str:
    status_url = escape(_build_status_callback_url())
    body = escape((reply_text[:700] if media_url else reply_text[:1200]))
    media_xml = f"<Media>{escape(media_url)}</Media>" if media_url else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<Response><Message action="{status_url}" method="POST" statusCallback="{status_url}">'
        f"<Body>{body}</Body>{media_xml}</Message></Response>"
    )


def _store_turn(from_number: str, role: str, content: str) -> None:
    repository.append_whatsapp_message(from_number, message=ChatMessage(role=role, content=content))


def _validate_twilio_signature(request: Request, form_data: dict) -> bool:
    if not settings.twilio_validate_signature or not settings.twilio_auth_token:
        return True
    signature = request.headers.get("X-Twilio-Signature")
    if not signature:
        return False
    validator = RequestValidator(settings.twilio_auth_token)
    return validator.validate(str(request.url), form_data, signature)


@router.get("/media/{media_id}")
async def whatsapp_media(media_id: str):
    """Serve temporary audio replies for Twilio media delivery."""
    payload = repository.get_whatsapp_media(media_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Media not found or expired")
    return Response(content=payload["content"], media_type=payload["content_type"])


@router.post("/status-callback")
async def whatsapp_status_callback(request: Request):
    """
    Receive Twilio message lifecycle callbacks.

    Twilio posts form-encoded fields such as MessageSid, MessageStatus,
    ErrorCode, ChannelStatusMessage, To, and From. The exact set can vary.
    """
    form = await request.form()
    payload = {key: value for key, value in form.items()}
    event = repository.record_whatsapp_status_event(payload)
    return {"received": True, "message_sid": event.get("MessageSid"), "status": event.get("MessageStatus")}


@router.get("/status-callback/recent")
async def whatsapp_status_recent(limit: int = 20):
    """Inspect recent Twilio status callbacks during development/demo."""
    return {"events": repository.get_whatsapp_status_events(limit=limit)}


@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(default=""),
    NumMedia: int = Form(default=0),
    MediaUrl0: str = Form(default=""),
    MediaContentType0: str = Form(default=""),
):
    """
    Twilio WhatsApp webhook endpoint.

    Supports:
    - Text messages
    - Voice notes with STT attempt, TTS/media reply attempt, and text fallback
    """
    try:
        form_data = {
            "From": From,
            "Body": Body,
            "NumMedia": str(NumMedia),
            "MediaUrl0": MediaUrl0,
            "MediaContentType0": MediaContentType0,
        }
        if not _validate_twilio_signature(request, form_data):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")

        user_text = Body.strip()
        received_voice = False

        if NumMedia > 0 and MediaContentType0.startswith("audio/") and MediaUrl0:
            received_voice = True
            audio_bytes = await download_audio(MediaUrl0)
            user_text = await _transcribe_audio(audio_bytes)
            if not user_text:
                return Response(
                    content=_build_whatsapp_response(_voice_retry_message()),
                    media_type="application/xml",
                )

        if not user_text:
            intro = (
                "Namaste, I am VikasGPT. Send your health problem as text or voice note.\n\n"
                "नमस्ते, मैं विकास-GPT हूं। अपनी स्वास्थ्य समस्या text या voice note में भेजें।"
            )
            return Response(content=_build_whatsapp_response(intro), media_type="application/xml")

        _store_turn(From, "user", user_text)
        route_response = orchestrator.route_turn(
            session_id=f"wa-{From.replace(':', '-').replace('+', '')}",
            channel="whatsapp",
            message=user_text,
            household_id=None,
            language="hi",
            force_agent=AgentType.HEALTH if received_voice else None,
            whatsapp_from_number=From,
        )
        reply_text = route_response.reply_text
        _store_turn(From, "assistant", reply_text)

        media_url = None
        if received_voice:
            media_url = await _create_voice_reply_url(reply_text)

        return Response(
            content=_build_whatsapp_response(reply_text, media_url=media_url),
            media_type="application/xml",
        )
    except Exception as exc:
        print(f"WhatsApp webhook error: {exc}")
        fallback = (
            "Sorry, something went wrong. Please try again in a moment or send your message as text.\n\n"
            "माफ़ कीजिए, कुछ गड़बड़ हो गई। कृपया थोड़ी देर बाद फिर कोशिश करें या अपना सवाल text में भेजें।"
        )
        return Response(
            content=_build_whatsapp_response(fallback),
            media_type="application/xml",
        )
