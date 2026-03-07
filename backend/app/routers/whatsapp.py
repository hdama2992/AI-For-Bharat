"""
WhatsApp webhook and temporary media hosting for the prototype.
"""
import base64
import binascii
from xml.sax.saxutils import escape

import httpx
from fastapi import APIRouter, Form, HTTPException, Request, Response

from app.config import get_settings
from app.db.memory import (
    append_whatsapp_message,
    get_whatsapp_media,
    get_whatsapp_session,
    get_whatsapp_status_events,
    record_whatsapp_status_event,
    store_whatsapp_media,
)
from app.models.health import ChatMessage
from app.services.bhashini import bhashini_service
from app.services.health_advisor import health_advisor

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
    audio_b64 = base64.standard_b64encode(audio_bytes).decode("utf-8")
    transcript = await bhashini_service.speech_to_text(
        audio_base64=audio_b64,
        source_lang="hi",
    )
    if not transcript or transcript.startswith("["):
        return ""
    return transcript.strip()


async def _create_voice_reply_url(text: str) -> str | None:
    audio_b64 = await bhashini_service.text_to_speech(
        text=text,
        target_lang="hi",
        gender="female",
    )
    if not audio_b64:
        return None

    try:
        audio_bytes = base64.b64decode(audio_b64)
    except (binascii.Error, ValueError):
        return None

    media_id = store_whatsapp_media(audio_bytes, "audio/wav")
    return _build_media_url(media_id)


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
    append_whatsapp_message(from_number, ChatMessage(role=role, content=content))


@router.get("/media/{media_id}")
async def whatsapp_media(media_id: str):
    """Serve temporary audio replies for Twilio media delivery."""
    payload = get_whatsapp_media(media_id)
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
    event = record_whatsapp_status_event(payload)
    return {"received": True, "message_sid": event.get("MessageSid"), "status": event.get("MessageStatus")}


@router.get("/status-callback/recent")
async def whatsapp_status_recent(limit: int = 20):
    """Inspect recent Twilio status callbacks during development/demo."""
    return {"events": get_whatsapp_status_events(limit=limit)}


@router.post("/webhook")
async def whatsapp_webhook(
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

        history = get_whatsapp_session(From)
        _store_turn(From, "user", user_text)

        reply = health_advisor.generate_reply(
            user_message=user_text,
            conversation_history=history,
            household_context=None,
            language="hi",
        )
        _store_turn(From, "assistant", reply.display_text)

        media_url = None
        if received_voice:
            media_url = await _create_voice_reply_url(reply.display_text)

        return Response(
            content=_build_whatsapp_response(reply.display_text, media_url=media_url),
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
