"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    app_name: str = "VikasGPT"
    debug: bool = True
    api_version: str = "v1"
    public_base_url: str = "http://localhost:8000"

    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # AWS
    aws_region: str = "ap-south-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_bearer_token_bedrock: Optional[str] = None
    aws_session_token: Optional[str] = None

    # Bedrock
    bedrock_model_id: str = "anthropic.claude-sonnet-4-20250514-v1:0"
    bedrock_haiku_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    bedrock_supervisor_model_id: Optional[str] = None
    bedrock_onboarding_model_id: Optional[str] = None
    bedrock_mandi_model_id: Optional[str] = None
    bedrock_temperature: float = 0.4
    bedrock_router_temperature: float = 0.1

    # Legacy Bhashini API settings (unused in the Sarvam-first path)
    bhashini_user_id: Optional[str] = None
    bhashini_api_key: Optional[str] = None
    bhashini_pipeline_url: str = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
    bhashini_inference_url: str = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

    # Speech provider
    speech_provider: str = "sarvam"

    # Sarvam API
    sarvam_api_key: Optional[str] = None
    sarvam_base_url: str = "https://api.sarvam.ai"
    sarvam_stt_model: str = "saaras:v3"
    sarvam_tts_model: str = "bulbul:v3"
    sarvam_translate_model: str = "sarvam-translate:v1"
    sarvam_tts_speaker: str = "shubh"
    sarvam_tts_sample_rate: int = 24000

    # Storage
    use_dynamodb: bool = True
    dynamodb_table_prefix: str = "vikasgpt_"
    s3_media_bucket: Optional[str] = None
    s3_media_prefix: str = "whatsapp-media/"
    s3_media_ttl_seconds: int = 900

    # Twilio WhatsApp
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_number: str = "whatsapp:+14155238886"
    twilio_validate_signature: bool = True

    # DPI (Digital Public Infrastructure) API Keys
    data_gov_api_key: str = ""  # data.gov.in API key for AGMARKNET

    # ABDM (Ayushman Bharat Digital Mission) Sandbox
    abdm_client_id: Optional[str] = None  # ABDM sandbox client ID
    abdm_client_secret: Optional[str] = None  # ABDM sandbox client secret
    abdm_sandbox_url: str = "https://abhasbx.abdm.gov.in"  # Sandbox base URL

    @property
    def supervisor_model_id(self) -> str:
        return self.bedrock_supervisor_model_id or self.bedrock_haiku_model_id

    @property
    def onboarding_model_id(self) -> str:
        return self.bedrock_onboarding_model_id or self.bedrock_haiku_model_id

    @property
    def mandi_model_id(self) -> str:
        return self.bedrock_mandi_model_id or self.bedrock_haiku_model_id


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
