"""
Bhashini API Integration for Indian Language AI Services
- Speech-to-Text (ASR)
- Text-to-Speech (TTS)
- Translation (NMT)

Supports 22 scheduled Indian languages.
"""
import httpx
import base64
from typing import Optional, Literal
from app.config import get_settings

settings = get_settings()

# Language codes for Bhashini
LANGUAGE_CODES = {
    "en": "en",
    "hi": "hi",
    "ta": "ta",  # Tamil
    "te": "te",  # Telugu
    "kn": "kn",  # Kannada
    "ml": "ml",  # Malayalam
    "mr": "mr",  # Marathi
    "bn": "bn",  # Bengali
    "gu": "gu",  # Gujarati
    "pa": "pa",  # Punjabi
    "or": "or",  # Odia
    "as": "as",  # Assamese
}


class BhashiniService:
    """Bhashini API client for Indian language processing"""
    
    def __init__(self):
        self.user_id = settings.bhashini_user_id
        self.api_key = settings.bhashini_api_key
        self.pipeline_url = settings.bhashini_pipeline_url
        self.inference_url = settings.bhashini_inference_url
        self._pipeline_cache = {}
    
    def _get_headers(self) -> dict:
        """Get authorization headers"""
        return {
            "Content-Type": "application/json",
            "userID": self.user_id or "",
            "ulcaApiKey": self.api_key or "",
        }
    
    async def get_pipeline(
        self,
        task: Literal["asr", "tts", "translation"],
        source_lang: str,
        target_lang: Optional[str] = None,
    ) -> dict:
        """Get pipeline configuration for a task"""
        cache_key = f"{task}:{source_lang}:{target_lang}"
        if cache_key in self._pipeline_cache:
            return self._pipeline_cache[cache_key]
        
        payload = {
            "pipelineTasks": [{"taskType": task, "config": {"language": {"sourceLanguage": source_lang}}}],
            "pipelineRequestConfig": {"pipelineId": "64392f96daac500b55c543cd"},
        }
        
        if target_lang and task == "translation":
            payload["pipelineTasks"][0]["config"]["language"]["targetLanguage"] = target_lang
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.pipeline_url, headers=self._get_headers(), json=payload)
            if resp.status_code == 200:
                data = resp.json()
                self._pipeline_cache[cache_key] = data
                return data
        return {}
    
    async def speech_to_text(self, audio_base64: str, source_lang: str = "hi") -> str:
        """Convert speech audio to text (ASR)"""
        if not self.api_key:
            return "[Bhashini API key not configured]"
        
        pipeline = await self.get_pipeline("asr", source_lang)
        if not pipeline:
            return "[Failed to get ASR pipeline]"
        
        service_id = pipeline.get("pipelineResponseConfig", [{}])[0].get("config", [{}])[0].get("serviceId", "")
        callback_url = pipeline.get("pipelineInferenceAPIEndPoint", {}).get("callbackUrl", self.inference_url)
        
        payload = {
            "pipelineTasks": [{
                "taskType": "asr",
                "config": {"language": {"sourceLanguage": source_lang}, "serviceId": service_id}
            }],
            "inputData": {"audio": [{"audioContent": audio_base64}]}
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(callback_url, headers=self._get_headers(), json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("pipelineResponse", [{}])[0].get("output", [{}])[0].get("source", "")
        return ""
    
    async def text_to_speech(self, text: str, target_lang: str = "hi", gender: str = "female") -> str:
        """Convert text to speech audio (TTS). Returns base64 audio."""
        if not self.api_key:
            return ""
        
        pipeline = await self.get_pipeline("tts", target_lang)
        if not pipeline:
            return ""
        
        service_id = pipeline.get("pipelineResponseConfig", [{}])[0].get("config", [{}])[0].get("serviceId", "")
        callback_url = pipeline.get("pipelineInferenceAPIEndPoint", {}).get("callbackUrl", self.inference_url)
        
        payload = {
            "pipelineTasks": [{
                "taskType": "tts",
                "config": {"language": {"sourceLanguage": target_lang}, "serviceId": service_id, "gender": gender}
            }],
            "inputData": {"input": [{"source": text}]}
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(callback_url, headers=self._get_headers(), json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("pipelineResponse", [{}])[0].get("audio", [{}])[0].get("audioContent", "")
        return ""
    
    async def translate(self, text: str, source_lang: str = "hi", target_lang: str = "en") -> str:
        """Translate text between languages (NMT)"""
        if not self.api_key:
            return text  # Return original if not configured
        
        if source_lang == target_lang:
            return text
        
        pipeline = await self.get_pipeline("translation", source_lang, target_lang)
        if not pipeline:
            return text
        
        service_id = pipeline.get("pipelineResponseConfig", [{}])[0].get("config", [{}])[0].get("serviceId", "")
        callback_url = pipeline.get("pipelineInferenceAPIEndPoint", {}).get("callbackUrl", self.inference_url)
        
        payload = {
            "pipelineTasks": [{
                "taskType": "translation",
                "config": {"language": {"sourceLanguage": source_lang, "targetLanguage": target_lang}, "serviceId": service_id}
            }],
            "inputData": {"input": [{"source": text}]}
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(callback_url, headers=self._get_headers(), json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("pipelineResponse", [{}])[0].get("output", [{}])[0].get("target", text)
        return text


# Singleton instance
bhashini_service = BhashiniService()

