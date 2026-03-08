"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App
    app_name: str = "VikasGPT"
    debug: bool = True
    api_version: str = "v1"
    public_base_url: str = "http://localhost:8000"
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # AWS Settings
    aws_region: str = "ap-south-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_bearer_token_bedrock: Optional[str] = None
    
    # Bedrock (auth via AWS_BEARER_TOKEN_BEDROCK env var)
    bedrock_model_id: str = "global.anthropic.claude-opus-4-6-v1"
    bedrock_haiku_model_id: str = "global.anthropic.claude-opus-4-6-v1"
    
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
    sarvam_tts_speaker: str = "Shubh"
    sarvam_tts_sample_rate: int = 24000

    # DynamoDB (optional - use in-memory for prototype)
    use_dynamodb: bool = False
    dynamodb_table_prefix: str = "vikasgpt_"

    # Twilio WhatsApp
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_number: str = "whatsapp:+14155238886"  # Sandbox default

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
