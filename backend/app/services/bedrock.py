"""
Amazon Bedrock service for Claude AI integration.
Auth via AWS_BEARER_TOKEN_BEDROCK env var (Bedrock API key) — picked up by boto3 automatically.
"""
from __future__ import annotations

import json
import os
from typing import Dict, Generator, List, Optional

import boto3
from app.config import get_settings

settings = get_settings()
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")


class BedrockService:
    """Amazon Bedrock client using boto3."""

    def __init__(self):
        self.runtime_client = None
        self._init_client()

    def _init_client(self):
        try:
            # Ensure AWS_BEARER_TOKEN_BEDROCK is in os.environ for boto3
            if settings.aws_bearer_token_bedrock:
                os.environ["AWS_BEARER_TOKEN_BEDROCK"] = settings.aws_bearer_token_bedrock
            kwargs: dict = {"region_name": settings.aws_region}
            if settings.aws_access_key_id and settings.aws_secret_access_key:
                kwargs["aws_access_key_id"] = settings.aws_access_key_id
                kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
            if settings.aws_session_token:
                kwargs["aws_session_token"] = settings.aws_session_token
            session = boto3.Session(**kwargs)
            self.runtime_client = session.client("bedrock-runtime")
        except Exception as e:
            print(f"Warning: Could not initialize Bedrock client: {e}")

    def is_configured(self) -> bool:
        return self.runtime_client is not None

    def _build_body(self, messages, system_prompt, max_tokens, temperature):
        body: dict = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system_prompt:
            body["system"] = system_prompt
        return body

    def invoke(
        self,
        messages: List[Dict],
        system_prompt: str = "",
        model_id: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        if not self.runtime_client:
            return "[Bedrock not configured.]"
        model = model_id or settings.bedrock_model_id
        body = self._build_body(messages, system_prompt, max_tokens, temperature)
        try:
            resp = self.runtime_client.invoke_model(
                modelId=model,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            result = json.loads(resp["body"].read())
            return result.get("content", [{}])[0].get("text", "")
        except Exception as e:
            return f"[Error calling Bedrock: {e}]"

    def invoke_stream(
        self,
        messages: List[Dict],
        system_prompt: str = "",
        model_id: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """Simulate streaming by chunking non-streaming response.
        Bedrock API keys don't support invoke_model_with_response_stream."""
        result = self.invoke(
            messages=messages,
            system_prompt=system_prompt,
            model_id=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        # Yield in small chunks to simulate streaming
        chunk_size = 60
        for i in range(0, len(result), chunk_size):
            yield result[i:i + chunk_size]

    def invoke_haiku(self, messages: List[Dict], system_prompt: str = "") -> str:
        return self.invoke(
            messages=messages,
            system_prompt=system_prompt,
            model_id=settings.bedrock_haiku_model_id,
            max_tokens=1024,
            temperature=0.3,
        )


bedrock_service = BedrockService()
