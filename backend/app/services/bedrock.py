"""
Amazon Bedrock service for Claude AI integration
Supports streaming responses for health chat
"""
import json
import boto3
from typing import AsyncGenerator, List, Dict, Optional
from app.config import get_settings

settings = get_settings()


class BedrockService:
    """Amazon Bedrock client for Claude models"""
    
    def __init__(self):
        self.client = None
        self.runtime_client = None
        self._init_clients()
    
    def _init_clients(self):
        """Initialize Bedrock clients"""
        try:
            session_kwargs = {"region_name": settings.aws_region}
            if settings.aws_access_key_id and settings.aws_secret_access_key:
                session_kwargs["aws_access_key_id"] = settings.aws_access_key_id
                session_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
            
            session = boto3.Session(**session_kwargs)
            self.runtime_client = session.client("bedrock-runtime")
        except Exception as e:
            print(f"Warning: Could not initialize Bedrock client: {e}")
            self.runtime_client = None
    
    def invoke(
        self,
        messages: List[Dict],
        system_prompt: str = "",
        model_id: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """Invoke Claude model and return full response"""
        if not self.runtime_client:
            return "[Bedrock not configured. Please set AWS credentials.]"
        
        model = model_id or settings.bedrock_model_id
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        
        if system_prompt:
            body["system"] = system_prompt
        
        try:
            response = self.runtime_client.invoke_model(
                modelId=model,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            
            result = json.loads(response["body"].read())
            return result.get("content", [{}])[0].get("text", "")
        except Exception as e:
            return f"[Error calling Bedrock: {str(e)}]"
    
    def invoke_stream(
        self,
        messages: List[Dict],
        system_prompt: str = "",
        model_id: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ):
        """Invoke Claude model with streaming response (generator)"""
        if not self.runtime_client:
            yield "[Bedrock not configured. Please set AWS credentials.]"
            return
        
        model = model_id or settings.bedrock_model_id
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        
        if system_prompt:
            body["system"] = system_prompt
        
        try:
            response = self.runtime_client.invoke_model_with_response_stream(
                modelId=model,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            
            for event in response.get("body", []):
                chunk = event.get("chunk")
                if chunk:
                    data = json.loads(chunk.get("bytes", b"{}").decode())
                    if data.get("type") == "content_block_delta":
                        delta = data.get("delta", {})
                        if delta.get("type") == "text_delta":
                            yield delta.get("text", "")
        except Exception as e:
            yield f"[Error streaming from Bedrock: {str(e)}]"
    
    def invoke_haiku(self, messages: List[Dict], system_prompt: str = "") -> str:
        """Use faster Haiku model for extraction tasks"""
        return self.invoke(
            messages=messages,
            system_prompt=system_prompt,
            model_id=settings.bedrock_haiku_model_id,
            max_tokens=1024,
            temperature=0.3,
        )


# Singleton instance
bedrock_service = BedrockService()

