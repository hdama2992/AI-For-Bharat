"""
Provider-based speech services.

Sarvam is the primary provider for STT/TTS/translation.
"""
from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from typing import Dict, Optional

import httpx

from app.config import get_settings

settings = get_settings()


LANGUAGE_CODE_MAP: Dict[str, str] = {
    "en": "en-IN",
    "hi": "hi-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "mr": "mr-IN",
    "bn": "bn-IN",
    "gu": "gu-IN",
    "pa": "pa-IN",
    "or": "od-IN",
    "as": "as-IN",
}

SUPPORTED_LANGUAGE_METADATA = [
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


def normalize_language_code(language_code: str) -> str:
    return LANGUAGE_CODE_MAP.get(language_code, language_code)


def denormalize_language_code(language_code: str) -> str:
    for short_code, long_code in LANGUAGE_CODE_MAP.items():
        if long_code == language_code:
            return short_code
    return language_code


class SpeechProviderError(RuntimeError):
    """Speech provider failure."""


class BaseSpeechProvider(ABC):
    @abstractmethod
    async def speech_to_text(self, audio_bytes: bytes, source_lang: str = "hi") -> str:
        raise NotImplementedError

    @abstractmethod
    async def text_to_speech(self, text: str, target_lang: str = "hi", gender: str = "female") -> str:
        raise NotImplementedError

    @abstractmethod
    async def translate(self, text: str, source_lang: str = "hi", target_lang: str = "en") -> str:
        raise NotImplementedError

    @abstractmethod
    def get_supported_languages(self) -> list[dict]:
        raise NotImplementedError


class SarvamSpeechProvider(BaseSpeechProvider):
    """Sarvam REST API client."""

    def __init__(self):
        self.api_key = settings.sarvam_api_key
        self.base_url = settings.sarvam_base_url.rstrip("/")
        self.stt_model = settings.sarvam_stt_model
        self.tts_model = settings.sarvam_tts_model
        self.translate_model = settings.sarvam_translate_model
        self.tts_speaker = settings.sarvam_tts_speaker
        self.tts_sample_rate = settings.sarvam_tts_sample_rate

    def _headers(self, content_type: Optional[str] = "application/json") -> dict:
        headers = {"api-subscription-key": self.api_key or ""}
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _ensure_configured(self):
        if not self.api_key:
            raise SpeechProviderError("Sarvam API key not configured.")

    async def speech_to_text(self, audio_bytes: bytes, source_lang: str = "hi") -> str:
        self._ensure_configured()
        files = {
            "file": ("audio.wav", audio_bytes, "audio/wav"),
        }
        data = {
            "language_code": normalize_language_code(source_lang),
            "model": self.stt_model,
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{self.base_url}/speech-to-text",
                headers=self._headers(content_type=None),
                data=data,
                files=files,
            )
        if response.status_code >= 400:
            raise SpeechProviderError(f"Sarvam STT failed: {response.text}")
        payload = response.json()
        transcript = payload.get("transcript", "")
        if not transcript:
            raise SpeechProviderError("Sarvam STT returned an empty transcript.")
        return transcript.strip()

    async def text_to_speech(self, text: str, target_lang: str = "hi", gender: str = "female") -> str:
        self._ensure_configured()
        payload = {
            "inputs": [text],
            "target_language_code": normalize_language_code(target_lang),
            "speaker": self.tts_speaker,
            "model": self.tts_model,
            "speech_sample_rate": self.tts_sample_rate,
            "enable_preprocessing": True,
            "override_triplets": {},
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{self.base_url}/text-to-speech",
                headers=self._headers(),
                json=payload,
            )
        if response.status_code >= 400:
            raise SpeechProviderError(f"Sarvam TTS failed: {response.text}")
        body = response.json()
        audios = body.get("audios", [])
        if not audios:
            raise SpeechProviderError("Sarvam TTS returned no audio.")
        # Sarvam returns base64 audio strings; keep router contract unchanged.
        return audios[0]

    async def translate(self, text: str, source_lang: str = "hi", target_lang: str = "en") -> str:
        self._ensure_configured()
        if source_lang == target_lang:
            return text
        payload = {
            "input": text,
            "source_language_code": normalize_language_code(source_lang),
            "target_language_code": normalize_language_code(target_lang),
            "model": self.translate_model,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/translate",
                headers=self._headers(),
                json=payload,
            )
        if response.status_code >= 400:
            raise SpeechProviderError(f"Sarvam translate failed: {response.text}")
        body = response.json()
        translated = body.get("translated_text")
        if translated is None:
            raise SpeechProviderError("Sarvam translate returned no translated text.")
        return translated

    def get_supported_languages(self) -> list[dict]:
        return SUPPORTED_LANGUAGE_METADATA


def get_speech_provider() -> BaseSpeechProvider:
    provider = settings.speech_provider.lower()
    if provider == "sarvam":
        return SarvamSpeechProvider()
    raise SpeechProviderError(f"Unsupported speech provider: {settings.speech_provider}")


speech_provider = get_speech_provider()
