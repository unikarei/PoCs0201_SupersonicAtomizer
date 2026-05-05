"""Case-aware chat endpoints for the FastAPI GUI (P34-T05)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from supersonic_atomizer.gui.case_store import CaseNameError, CaseNotFoundError, CaseStore
from supersonic_atomizer.gui.chat_history_store import ChatHistoryStore, ChatThreadNotFoundError
from supersonic_atomizer.gui.chat_service import ChatConfigurationError, ChatService
from supersonic_atomizer.gui.schemas import (
    ChatMessage,
    ChatReplyResponse,
    ChatRequest,
    ChatSummaryRequest,
    ChatSummaryResponse,
    ChatThreadCreateRequest,
    ChatThreadDetail,
    ChatThreadListResponse,
    ChatThreadMessagesUpdateRequest,
    ChatThreadRenameRequest,
    ChatThreadSummary,
)

router = APIRouter()
_chat_service = ChatService()
_chat_history_store = ChatHistoryStore()


def _get_store() -> CaseStore:
    return CaseStore()


def _ensure_case_exists(store: CaseStore, case_name: str, project_name: str | None) -> dict:
    if not store.exists(case_name, project=project_name):
        raise HTTPException(status_code=404, detail=f"Case {case_name!r} not found.")
    return store.load(case_name, project=project_name)


def _normalize_messages(messages: list[ChatMessage]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for message in messages:
        if message.role not in {"user", "assistant", "system"}:
            continue
        normalized.append({"role": message.role, "content": message.content})
    return normalized


def _thread_detail_payload(thread: dict) -> ChatThreadDetail:
    return ChatThreadDetail(
        id=thread["id"],
        title=thread["title"],
        created_at=thread["created_at"],
        updated_at=thread["updated_at"],
        messages=[ChatMessage(role=m.get("role", "assistant"), content=m.get("content", "")) for m in thread.get("messages", [])],
    )


@router.get("/threads", response_model=ChatThreadListResponse)
async def list_chat_threads(case_name: str, project_name: str | None = None) -> ChatThreadListResponse:
    """List persisted chat threads for the selected case."""
    store = _get_store()
    try:
        _ensure_case_exists(store, case_name, project_name)
    except CaseNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    summaries = _chat_history_store.list_threads(project_name, case_name)
    threads = [ChatThreadSummary(**summary) for summary in summaries]
    return ChatThreadListResponse(threads=threads)


@router.post("/threads", response_model=ChatThreadDetail, status_code=201)
async def create_chat_thread(body: ChatThreadCreateRequest) -> ChatThreadDetail:
    """Create a new chat thread for the selected case."""
    store = _get_store()
    try:
        _ensure_case_exists(store, body.case_name, body.project_name)
    except CaseNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    thread = _chat_history_store.create_thread(body.project_name, body.case_name, title=body.title)
    return _thread_detail_payload(thread)


@router.get("/threads/{thread_id}", response_model=ChatThreadDetail)
async def get_chat_thread(thread_id: str, case_name: str, project_name: str | None = None) -> ChatThreadDetail:
    """Load a persisted chat thread with full message history."""
    store = _get_store()
    try:
        _ensure_case_exists(store, case_name, project_name)
        thread = _chat_history_store.get_thread(project_name, case_name, thread_id)
    except CaseNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ChatThreadNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _thread_detail_payload(thread)


@router.patch("/threads/{thread_id}", response_model=ChatThreadDetail)
async def rename_chat_thread(thread_id: str, body: ChatThreadRenameRequest) -> ChatThreadDetail:
    """Rename a persisted chat thread."""
    store = _get_store()
    try:
        _ensure_case_exists(store, body.case_name, body.project_name)
        thread = _chat_history_store.rename_thread(
            body.project_name,
            body.case_name,
            thread_id,
            title=body.title,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CaseNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ChatThreadNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _thread_detail_payload(thread)


@router.delete("/threads/{thread_id}", status_code=204)
async def delete_chat_thread(thread_id: str, case_name: str, project_name: str | None = None) -> None:
    """Delete a persisted chat thread."""
    store = _get_store()
    try:
        _ensure_case_exists(store, case_name, project_name)
        _chat_history_store.delete_thread(project_name, case_name, thread_id)
    except CaseNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ChatThreadNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/threads/{thread_id}/messages", response_model=ChatThreadDetail)
async def replace_chat_thread_messages(thread_id: str, body: ChatThreadMessagesUpdateRequest) -> ChatThreadDetail:
    """Replace full message history for a thread (used by clear/reset flows)."""
    store = _get_store()
    try:
        _ensure_case_exists(store, body.case_name, body.project_name)
        thread = _chat_history_store.set_thread_messages(
            body.project_name,
            body.case_name,
            thread_id,
            messages=_normalize_messages(body.messages),
        )
    except CaseNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ChatThreadNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _thread_detail_payload(thread)


@router.post("/messages", response_model=ChatReplyResponse)
async def send_chat_message(request: Request, body: ChatRequest) -> ChatReplyResponse:
    """Return a case-aware assistant reply for the selected case."""
    store = _get_store()
    thread = None
    thread_id = body.thread_id
    try:
        case_config = _ensure_case_exists(store, body.case_name, body.project_name)
        if thread_id:
            thread = _chat_history_store.get_thread(body.project_name, body.case_name, thread_id)
        else:
            title_seed = next((m.content.strip() for m in body.messages if m.role == "user" and m.content.strip()), "")
            thread = _chat_history_store.create_thread(
                body.project_name,
                body.case_name,
                title=title_seed[:48] if title_seed else "New chat",
            )
            thread_id = thread["id"]
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CaseNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ChatThreadNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # Allow optional per-request model override via X-LLM-MODEL header
    model_override = None
    try:
        model_override = request.headers.get("X-LLM-MODEL")
    except Exception:
        model_override = None

    try:
        normalized_messages = _normalize_messages(body.messages)
        reply_text = _chat_service.generate_reply(
            project_name=body.project_name,
            case_name=body.case_name,
            case_config=case_config,
            messages=normalized_messages,
            model_override=model_override,
        )
        persisted = [*normalized_messages, {"role": "assistant", "content": reply_text}]
        if thread_id:
            thread = _chat_history_store.set_thread_messages(
                body.project_name,
                body.case_name,
                thread_id,
                messages=persisted,
            )
    except ChatConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ChatReplyResponse(
        reply=ChatMessage(role="assistant", content=reply_text),
        thread_id=thread_id,
        thread_title=(thread or {}).get("title") if isinstance(thread, dict) else None,
    )


@router.post("/summary", response_model=ChatSummaryResponse)
async def generate_chat_summary(request: Request, body: ChatSummaryRequest) -> ChatSummaryResponse:
    """Generate a concise summary of the current chat thread for the selected case."""
    store = _get_store()
    try:
        case_config = _ensure_case_exists(store, body.case_name, body.project_name)
        thread = _chat_history_store.get_thread(body.project_name, body.case_name, body.thread_id)
    except CaseNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ChatThreadNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    model_override: str | None = None
    try:
        model_override = request.headers.get("X-LLM-MODEL")
    except Exception:
        model_override = None

    messages = thread.get("messages", [])
    if not messages:
        return ChatSummaryResponse(summary="")

    # Build a summarization instruction as the final user turn.
    refine_clause = f"\n\nAdditional instruction: {body.refine_prompt}" if body.refine_prompt else ""
    summary_instruction = (
        f"Summarize the conversation above in no more than {body.max_chars} characters. "
        "Use concise, technically specific language appropriate for an engineering audience."
        f"{refine_clause}"
    )

    summary_messages = [*_normalize_messages(
        [ChatMessage(role=m.get("role", "assistant"), content=m.get("content", "")) for m in messages]
    ), {"role": "user", "content": summary_instruction}]

    try:
        summary_text = _chat_service.generate_reply(
            project_name=body.project_name,
            case_name=body.case_name,
            case_config=case_config,
            messages=summary_messages,
            model_override=model_override,
        )
    except ChatConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ChatSummaryResponse(summary=summary_text)