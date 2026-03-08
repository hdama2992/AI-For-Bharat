"""DynamoDB and S3-backed persistence for prototype sessions and media."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
import os
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings

settings = get_settings()
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")


def _to_decimal(value: Any) -> Any:
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, list):
        return [_to_decimal(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_decimal(item) for key, item in value.items()}
    return value


def _from_decimal(value: Any) -> Any:
    if isinstance(value, Decimal):
        if value % 1 == 0:
            return int(value)
        return float(value)
    if isinstance(value, list):
        return [_from_decimal(item) for item in value]
    if isinstance(value, dict):
        return {key: _from_decimal(item) for key, item in value.items()}
    return value


class DynamoDBStore:
    """Thin persistence wrapper with graceful failure handling."""

    def __init__(self) -> None:
        self.enabled = settings.use_dynamodb
        self._dynamodb_resource = None
        self._s3_client = None
        if not self.enabled:
            return

        try:
            kwargs: dict[str, Any] = {"region_name": settings.aws_region}
            if settings.aws_access_key_id and settings.aws_secret_access_key:
                kwargs["aws_access_key_id"] = settings.aws_access_key_id
                kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
            if settings.aws_session_token:
                kwargs["aws_session_token"] = settings.aws_session_token
            session = boto3.Session(**kwargs)
            self._dynamodb_resource = session.resource("dynamodb")
            if settings.s3_media_bucket:
                self._s3_client = session.client("s3")
        except Exception as exc:  # pragma: no cover - startup environment dependent
            print(f"Warning: could not initialize DynamoDB/S3 store: {exc}")
            self.enabled = False

    def is_ready(self) -> bool:
        return self.enabled and self._dynamodb_resource is not None

    def supports_s3(self) -> bool:
        return self.is_ready() and self._s3_client is not None and bool(settings.s3_media_bucket)

    def _table(self, logical_name: str):
        table_name = f"{settings.dynamodb_table_prefix}{logical_name}"
        return self._dynamodb_resource.Table(table_name)

    def put_item(self, logical_name: str, item: Dict[str, Any]) -> None:
        self._table(logical_name).put_item(Item=_to_decimal(item))

    def get_item(self, logical_name: str, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        response = self._table(logical_name).get_item(Key=_to_decimal(key))
        item = response.get("Item")
        return _from_decimal(item) if item else None

    def query_items(
        self,
        logical_name: str,
        key_condition_expression,
        limit: int = 20,
        scan_index_forward: bool = False,
    ) -> List[Dict[str, Any]]:
        response = self._table(logical_name).query(
            KeyConditionExpression=key_condition_expression,
            Limit=limit,
            ScanIndexForward=scan_index_forward,
        )
        return [_from_decimal(item) for item in response.get("Items", [])]

    def list_items(self, logical_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        response = self._table(logical_name).scan(Limit=limit)
        return [_from_decimal(item) for item in response.get("Items", [])]

    def put_media(self, media_id: str, content: bytes, content_type: str, ttl_seconds: int) -> Dict[str, str]:
        if not self.supports_s3():
            raise RuntimeError("S3 media bucket is not configured.")
        key = f"{settings.s3_media_prefix}{media_id}.wav"
        self._s3_client.upload_fileobj(
            Fileobj=BytesIO(content),
            Bucket=settings.s3_media_bucket,
            Key=key,
            ExtraArgs={"ContentType": content_type},
        )
        return {
            "media_id": media_id,
            "bucket": settings.s3_media_bucket,
            "key": key,
            "content_type": content_type,
            "storage": "s3",
            "expires_at": (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat(),
        }

    def get_media_bytes(self, bucket: str, key: str) -> bytes:
        response = self._s3_client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()


dynamodb_store = DynamoDBStore()
