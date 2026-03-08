"""
Voice API Router for speech provider integration
- Speech-to-Text (ASR)
- Text-to-Speech (TTS)
- Translation
"""
import base64
import binascii

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal

from app.services.speech_provider import SpeechProviderError, speech_provider

router = APIRouter(prefix="/voice", tags=["Voice"])


class STTRequest(BaseModel):
    """Speech-to-Text request"""
    audio_base64: str
    source_language: str = "hi"  # Default Hindi


class STTResponse(BaseModel):
    """Speech-to-Text response"""
    text: str
    language: str


class TTSRequest(BaseModel):
    """Text-to-Speech request"""
    text: str
    target_language: str = "hi"
    gender: Literal["male", "female"] = "female"


class TTSResponse(BaseModel):
    """Text-to-Speech response"""
    audio_base64: str
    language: str


class TranslateRequest(BaseModel):
    """Translation request"""
    text: str
    source_language: str
    target_language: str


class TranslateResponse(BaseModel):
    """Translation response"""
    translated_text: str
    source_language: str
    target_language: str


@router.post("/stt", response_model=STTResponse)
async def speech_to_text(request: STTRequest):
    """Convert speech audio to text using the configured speech provider."""
    try:
        audio_bytes = base64.b64decode(request.audio_base64)
        text = await speech_provider.speech_to_text(
            audio_bytes=audio_bytes,
            source_lang=request.source_language,
        )
    except (ValueError, binascii.Error, SpeechProviderError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return STTResponse(text=text, language=request.source_language)


@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """Convert text to speech using the configured speech provider."""
    try:
        audio_b64 = await speech_provider.text_to_speech(
            text=request.text,
            target_lang=request.target_language,
            gender=request.gender,
        )
    except SpeechProviderError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return TTSResponse(audio_base64=audio_b64, language=request.target_language)


@router.post("/translate", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    """Translate text between languages using the configured speech provider."""
    try:
        translated = await speech_provider.translate(
            text=request.text,
            source_lang=request.source_language,
            target_lang=request.target_language,
        )
    except SpeechProviderError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    
    return TranslateResponse(
        translated_text=translated,
        source_language=request.source_language,
        target_language=request.target_language,
    )


@router.get("/languages")
async def get_supported_languages():
    """Get list of supported languages for the configured provider."""
    return {"languages": speech_provider.get_supported_languages()}
