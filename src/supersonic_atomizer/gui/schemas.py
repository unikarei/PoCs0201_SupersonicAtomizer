"""Pydantic request/response schemas for the FastAPI GUI layer (P25-T03).

Kept thin: only the shapes required by the REST API contract defined in
architecture.md Appendix B.7.2.  Heavy validation stays in the config layer.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class CaseCreateRequest(BaseModel):
    name: str


class ProjectCreateRequest(BaseModel):
    name: str


class CaseDuplicateRequest(BaseModel):
    new_name: str
    target_project: str | None = None


class CaseRenameRequest(BaseModel):
    new_name: str
    target_project: str | None = None


class ProjectRenameRequest(BaseModel):
    new_name: str


class RunRequest(BaseModel):
    case_name: str
    project_name: str | None = None
    config: dict[str, Any] = {}  # optional — case config already saved in CaseStore


class JobStatusResponse(BaseModel):
    status: str        # "running" | "completed" | "failed"
    error: str | None = None


class UnitUpdate(BaseModel):
    """Partial unit-preference update — only groups being changed need to be included."""
    model_config = {"extra": "allow"}


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    case_name: str
    project_name: str | None = None
    messages: list[ChatMessage]


class ChatReplyResponse(BaseModel):
    reply: ChatMessage
