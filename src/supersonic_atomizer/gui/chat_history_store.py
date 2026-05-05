"""Persistent chat-thread storage for case-aware GUI chat.

Stores thread metadata and message history per project/case in JSON files.
This module is GUI-layer persistence only (no solver logic).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import threading
import uuid
from typing import Any


_SAFE_COMPONENT_RE = re.compile(r"[^A-Za-z0-9_-]+")
_DEFAULT_HISTORY_DIR = Path("outputs") / "chat_histories"


class ChatThreadNotFoundError(KeyError):
    """Raised when the requested chat thread does not exist."""


@dataclass(frozen=True, slots=True)
class ChatThread:
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[dict[str, str]]


class ChatHistoryStore:
    """Thread-safe persistent JSON storage for case chat threads."""

    def __init__(self, root_dir: str | Path | None = None) -> None:
        self._root_dir = Path(root_dir) if root_dir is not None else _DEFAULT_HISTORY_DIR
        self._lock = threading.Lock()

    def _safe_component(self, value: str) -> str:
        safe = _SAFE_COMPONENT_RE.sub("_", value or "")
        return safe.strip("_") or "default"

    def _project_component(self, project_name: str | None) -> str:
        return self._safe_component(project_name or "default")

    def _case_component(self, case_name: str) -> str:
        return self._safe_component(case_name)

    def _threads_path(self, project_name: str | None, case_name: str) -> Path:
        return self._root_dir / self._project_component(project_name) / self._case_component(case_name) / "threads.json"

    def _ensure_parent_dir(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

    def _utc_now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def _sanitize_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        for message in messages:
            role = str(message.get("role", "")).strip()
            if role not in {"user", "assistant", "system"}:
                continue
            content = str(message.get("content", ""))
            normalized.append({"role": role, "content": content})
        return normalized

    def _load_threads(self, project_name: str | None, case_name: str) -> list[dict[str, Any]]:
        path = self._threads_path(project_name, case_name)
        if not path.exists():
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
        items = raw.get("threads", []) if isinstance(raw, dict) else []
        if not isinstance(items, list):
            return []

        normalized: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            thread_id = str(item.get("id", "")).strip()
            if not thread_id:
                continue
            title = str(item.get("title", "")).strip() or "New chat"
            created_at = str(item.get("created_at", "")).strip() or self._utc_now_iso()
            updated_at = str(item.get("updated_at", "")).strip() or created_at
            messages = self._sanitize_messages(item.get("messages", []) if isinstance(item.get("messages", []), list) else [])
            normalized.append(
                {
                    "id": thread_id,
                    "title": title,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "messages": messages,
                }
            )
        normalized.sort(key=lambda thread: thread.get("updated_at", ""), reverse=True)
        return normalized

    def _save_threads(self, project_name: str | None, case_name: str, threads: list[dict[str, Any]]) -> None:
        path = self._threads_path(project_name, case_name)
        self._ensure_parent_dir(path)
        payload = {"threads": threads}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _summary(self, thread: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": thread["id"],
            "title": thread["title"],
            "created_at": thread["created_at"],
            "updated_at": thread["updated_at"],
            "message_count": len(thread.get("messages", [])),
        }

    def list_threads(self, project_name: str | None, case_name: str) -> list[dict[str, Any]]:
        with self._lock:
            threads = self._load_threads(project_name, case_name)
            return [self._summary(thread) for thread in threads]

    def create_thread(self, project_name: str | None, case_name: str, *, title: str | None = None) -> dict[str, Any]:
        with self._lock:
            threads = self._load_threads(project_name, case_name)
            now = self._utc_now_iso()
            thread = {
                "id": uuid.uuid4().hex,
                "title": (title or "New chat").strip()[:120] or "New chat",
                "created_at": now,
                "updated_at": now,
                "messages": [],
            }
            threads.insert(0, thread)
            self._save_threads(project_name, case_name, threads)
            return dict(thread)

    def get_thread(self, project_name: str | None, case_name: str, thread_id: str) -> dict[str, Any]:
        with self._lock:
            threads = self._load_threads(project_name, case_name)
            for thread in threads:
                if thread["id"] == thread_id:
                    return dict(thread)
        raise ChatThreadNotFoundError(f"Chat thread {thread_id!r} not found.")

    def rename_thread(self, project_name: str | None, case_name: str, thread_id: str, *, title: str) -> dict[str, Any]:
        next_title = title.strip()[:120]
        if not next_title:
            raise ValueError("Thread title must not be empty.")

        with self._lock:
            threads = self._load_threads(project_name, case_name)
            for thread in threads:
                if thread["id"] != thread_id:
                    continue
                thread["title"] = next_title
                thread["updated_at"] = self._utc_now_iso()
                threads.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
                self._save_threads(project_name, case_name, threads)
                return dict(thread)
        raise ChatThreadNotFoundError(f"Chat thread {thread_id!r} not found.")

    def delete_thread(self, project_name: str | None, case_name: str, thread_id: str) -> None:
        with self._lock:
            threads = self._load_threads(project_name, case_name)
            kept = [thread for thread in threads if thread["id"] != thread_id]
            if len(kept) == len(threads):
                raise ChatThreadNotFoundError(f"Chat thread {thread_id!r} not found.")
            self._save_threads(project_name, case_name, kept)

    def set_thread_messages(
        self,
        project_name: str | None,
        case_name: str,
        thread_id: str,
        *,
        messages: list[dict[str, Any]],
        touch: bool = True,
    ) -> dict[str, Any]:
        with self._lock:
            threads = self._load_threads(project_name, case_name)
            for thread in threads:
                if thread["id"] != thread_id:
                    continue
                thread["messages"] = self._sanitize_messages(messages)
                if touch:
                    thread["updated_at"] = self._utc_now_iso()
                if (not thread.get("title") or thread["title"] == "New chat") and thread["messages"]:
                    for message in thread["messages"]:
                        if message.get("role") == "user" and message.get("content", "").strip():
                            thread["title"] = message["content"].strip().replace("\n", " ")[:48]
                            break
                threads.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
                self._save_threads(project_name, case_name, threads)
                return dict(thread)
        raise ChatThreadNotFoundError(f"Chat thread {thread_id!r} not found.")
