"""
Voice API Router for Bhashini Integration
- Speech-to-Text (ASR)
- Text-to-Speech (TTS)
- Translation
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional

from app.services.bhashini import bhashini_service

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
    """Convert speech audio to text using Bhashini ASR"""
    text = await bhashini_service.speech_to_text(
        audio_base64=request.audio_base64,
        source_lang=request.source_language,
    )
    
    if not text:
        raise HTTPException(status_code=500, detail="Failed to transcribe audio")
    
    return STTResponse(text=text, language=request.source_language)


@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """Convert text to speech audio using Bhashini TTS"""
    audio_b64 = await bhashini_service.text_to_speech(
        text=request.text,
        target_lang=request.target_language,
        gender=request.gender,
    )
    
    if not audio_b64:
        raise HTTPException(status_code=500, detail="Failed to generate speech")
    
    return TTSResponse(audio_base64=audio_b64, language=request.target_language)


@router.post("/translate", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    """Translate text between languages using Bhashini NMT"""
    translated = await bhashini_service.translate(
        text=request.text,
        source_lang=request.source_language,
        target_lang=request.target_language,
    )
    
    return TranslateResponse(
        translated_text=translated,
        source_language=request.source_language,
        target_language=request.target_language,
    )


@router.get("/languages")
async def get_supported_languages():
    """Get list of supported languages"""
    return {
        "languages": [
            {"code": "en", "name": "English", "name_native": "English"},
            {"code": "hi", "name": "Hindi", "name_native": "हिंदी"},
            {"code": "ta", "name": "Tamil", "name_native": "தமிழ்"},
            {"code": "te", "name": "Telugu", "name_native": "తెలుగు"},
            {"code": "kn", "name": "Kannada", "name_native": "ಕನ್ನಡ"},
            {"code": "ml", "name": "Malayalam", "name_native": "മലയാളം"},
            {"code": "mr", "name": "Marathi", "name_native": "मराठी"},
            {"code": "bn", "name": "Bengali", "name_native": "বাংলা"},
            {"code": "gu", "name": "Gujarati", "name_native": "ગુજરાતી"},
            {"code": "pa", "name": "Punjabi", "name_native": "ਪੰਜਾਬੀ"},
            {"code": "or", "name": "Odia", "name_native": "ଓଡ଼ିଆ"},
            {"code": "as", "name": "Assamese", "name_native": "অসমীয়া"},
        ]
    }

