"""Repository facade for household, session, WhatsApp, and media persistence."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional
import uuid

from boto3.dynamodb.conditions import Key

from app.db.dynamodb import dynamodb_store
from app.db.memory import (
    append_whatsapp_message,
    create_household as create_household_memory,
    get_agent_session as get_agent_session_memory,
    get_household as get_household_memory,
    get_whatsapp_media as get_whatsapp_media_memory,
    get_whatsapp_session as get_whatsapp_session_memory,
    get_whatsapp_status_events as get_whatsapp_status_events_memory,
    list_agent_sessions as list_agent_sessions_memory,
    record_whatsapp_status_event as record_whatsapp_status_event_memory,
    store_whatsapp_media as store_whatsapp_media_memory,
    update_household as update_household_memory,
    upsert_agent_session as upsert_agent_session_memory,
)
from app.models.chat import AgentSession, StoredMediaReference
from app.models.health import ChatMessage
from app.models.household import Household


class Repository:
    """Persistence facade with automatic memory fallback."""

    def __init__(self) -> None:
        self.store = dynamodb_store

    def _now(self) -> datetime:
        return datetime.utcnow()

    def create_household(self, data: dict) -> Household:
        if not self.store.is_ready():
            return create_household_memory(data)
        household_id = str(uuid.uuid4())[:12]
        household = Household(
            household_id=household_id,
            **data,
            created_at=self._now(),
            updated_at=self._now(),
        )
        try:
            self.store.put_item("households", household.model_dump(mode="json"))
            return household
        except Exception as exc:  # pragma: no cover - AWS dependent
            print(f"Falling back to memory household store: {exc}")
            return create_household_memory(data)

    def get_household(self, household_id: str) -> Optional[Household]:
        if not self.store.is_ready():
            return get_household_memory(household_id)
        try:
            item = self.store.get_item("households", {"household_id": household_id})
            return Household(**item) if item else None
        except Exception as exc:  # pragma: no cover - AWS dependent
            print(f"Falling back to memory household lookup: {exc}")
            return get_household_memory(household_id)

    def update_household(self, household_id: str, data: dict) -> Optional[Household]:
        household = self.get_household(household_id)
        if not household:
            return None
        for key, value in data.items():
            if hasattr(household, key):
                setattr(household, key, value)
        household.updated_at = self._now()
        if not self.store.is_ready():
            return update_household_memory(household_id, data)
        try:
            self.store.put_item("households", household.model_dump(mode="json"))
            return household
        except Exception as exc:  # pragma: no cover - AWS dependent
            print(f"Falling back to memory household update: {exc}")
            return update_household_memory(household_id, data)

    def get_agent_session(self, session_id: str) -> Optional[AgentSession]:
        if not self.store.is_ready():
            return get_agent_session_memory(session_id)
        try:
            item = self.store.get_item("agent_sessions", {"session_id": session_id})
            return AgentSession(**item) if item else None
        except Exception as exc:  # pragma: no cover - AWS dependent
            print(f"Falling back to memory agent session lookup: {exc}")
            return get_agent_session_memory(session_id)

    def upsert_agent_session(self, session: AgentSession) -> AgentSession:
        session.updated_at = self._now()
        if not self.store.is_ready():
            return upsert_agent_session_memory(session)
        try:
            self.store.put_item("agent_sessions", session.model_dump(mode="json"))
            return session
        except Exception as exc:  # pragma: no cover - AWS dependent
            print(f"Falling back to memory agent session store: {exc}")
            return upsert_agent_session_memory(session)

    def list_agent_sessions(self, household_id: Optional[str] = None, limit: int = 20) -> List[AgentSession]:
        if not self.store.is_ready():
            return list_agent_sessions_memory(household_id=household_id, limit=limit)
        try:
            items = self.store.list_items("agent_sessions", limit=max(limit, 50))
            sessions = [AgentSession(**item) for item in items]
            if household_id:
                sessions = [session for session in sessions if session.household_id == household_id]
            sessions.sort(key=lambda item: item.updated_at, reverse=True)
            return sessions[:limit]
        except Exception as exc:  # pragma: no cover - AWS dependent
            print(f"Falling back to memory session list: {exc}")
            return list_agent_sessions_memory(household_id=household_id, limit=limit)

    def get_whatsapp_session(self, from_number: str, limit: int = 10) -> List[ChatMessage]:
        if not self.store.is_ready():
            return get_whatsapp_session_memory(from_number)
        try:
            items = self.store.query_items(
                "whatsapp_sessions",
                Key("from_number").eq(from_number),
                limit=limit,
            )
            return [ChatMessage(role=item["role"], content=item["content"]) for item in reversed(items)]
        except Exception as exc:  # pragma: no cover - AWS dependent
            print(f"Falling back to memory WhatsApp session: {exc}")
            return get_whatsapp_session_memory(from_number)

    def append_whatsapp_message(self, from_number: str, message: ChatMessage, session_id: Optional[str] = None) -> List[ChatMessage]:
        if not self.store.is_ready():
            return append_whatsapp_message(from_number, message)
        try:
            record = {
                "from_number": from_number,
                "session_id": session_id or str(uuid.uuid4())[:12],
                "recorded_at": self._now().isoformat(),
                "role": message.role,
                "content": message.content,
            }
            self.store.put_item("whatsapp_sessions", record)
            return self.get_whatsapp_session(from_number)
        except Exception as exc:  # pragma: no cover - AWS dependent
            print(f"Falling back to memory WhatsApp append: {exc}")
            return append_whatsapp_message(from_number, message)

    def record_whatsapp_status_event(self, payload: dict) -> dict:
        event = {
            "message_sid": payload.get("MessageSid", str(uuid.uuid4())),
            "recorded_at": self._now().isoformat(),
            **payload,
        }
        if not self.store.is_ready():
            return record_whatsapp_status_event_memory(payload)
        try:
            self.store.put_item("whatsapp_status_events", event)
            return event
        except Exception as exc:  # pragma: no cover - AWS dependent
            print(f"Falling back to memory status event store: {exc}")
            return record_whatsapp_status_event_memory(payload)

    def get_whatsapp_status_events(self, limit: int = 50) -> List[dict]:
        if not self.store.is_ready():
            return get_whatsapp_status_events_memory(limit=limit)
        try:
            items = self.store.list_items("whatsapp_status_events", limit=max(limit, 100))
            items.sort(key=lambda item: item.get("recorded_at", ""), reverse=True)
            return items[:limit]
        except Exception as exc:  # pragma: no cover - AWS dependent
            print(f"Falling back to memory status event list: {exc}")
            return get_whatsapp_status_events_memory(limit=limit)

    def store_whatsapp_media(self, content: bytes, content_type: str, ttl_seconds: int = 900) -> StoredMediaReference:
        media_id = str(uuid.uuid4())
        if self.store.supports_s3():
            try:
                record = self.store.put_media(media_id, content, content_type, ttl_seconds)
                self.store.put_item("whatsapp_media", record)
                return StoredMediaReference(
                    media_id=media_id,
                    storage="s3",
                    content_type=content_type,
                    key=record["key"],
                )
            except Exception as exc:  # pragma: no cover - AWS dependent
                print(f"Falling back to memory media store: {exc}")
        fallback_media_id = store_whatsapp_media_memory(content, content_type, ttl_seconds=ttl_seconds)
        return StoredMediaReference(
            media_id=fallback_media_id,
            storage="memory",
            content_type=content_type,
        )

    def get_whatsapp_media(self, media_id: str) -> Optional[dict]:
        if self.store.is_ready():
            try:
                item = self.store.get_item("whatsapp_media", {"media_id": media_id})
                if item:
                    if item.get("storage") == "s3":
                        content = self.store.get_media_bytes(item["bucket"], item["key"])
                        return {"content": content, "content_type": item["content_type"]}
            except Exception as exc:  # pragma: no cover - AWS dependent
                print(f"Falling back to memory media lookup: {exc}")
        return get_whatsapp_media_memory(media_id)


repository = Repository()
