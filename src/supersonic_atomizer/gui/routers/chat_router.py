"""Case-aware chat endpoints for the FastAPI GUI (P34-T05)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from supersonic_atomizer.gui.case_store import CaseNameError, CaseNotFoundError, CaseStore
from supersonic_atomizer.gui.chat_change_workflow import (
    ChatChangeWorkflowStore,
    TERMINAL_PROPOSAL_STATES,
    apply_changes_with_validation,
    new_record,
)
from supersonic_atomizer.gui.chat_history_store import ChatHistoryStore, ChatThreadNotFoundError
from supersonic_atomizer.gui.chat_service import ChatConfigurationError, ChatService
from supersonic_atomizer.gui.schemas import (
    ChatConfigChangeApplyRequest,
    ChatConfigChangeConfirmRequest,
    ChatConfigChangeDiffItem,
    ChatConfigChangeItem,
    ChatConfigChangeProposalRequest,
    ChatConfigChangeProposalResponse,
    ChatConfigChangeRejectRequest,
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
_chat_change_store = ChatChangeWorkflowStore()


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


def _as_change_items(rows: list[dict[str, Any]]) -> list[ChatConfigChangeItem]:
    return [
        ChatConfigChangeItem(path=str(row.get("path", "")), value=row.get("value"))
        for row in rows
    ]


def _as_diff_items(rows: list[dict[str, Any]]) -> list[ChatConfigChangeDiffItem]:
    return [
        ChatConfigChangeDiffItem(
            path=str(row.get("path", "")),
            before=row.get("before"),
            after=row.get("after"),
        )
        for row in rows
    ]


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


@router.post("/config-changes/proposals", response_model=ChatConfigChangeProposalResponse)
async def create_chat_config_change_proposal(body: ChatConfigChangeProposalRequest) -> ChatConfigChangeProposalResponse:
    """Create a chat-driven Conditions/Grid change proposal for patterns 1-5."""
    store = _get_store()
    try:
        base_config = _ensure_case_exists(store, body.case_name, body.project_name)
    except CaseNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if body.pattern not in {1, 2, 3, 4, 5}:
        raise HTTPException(status_code=400, detail="pattern must be one of: 1, 2, 3, 4, 5")

    changes_payload = [change.model_dump() for change in body.changes]

    # Pattern 1 is advisory-only: no mutable payload, no lifecycle state.
    if body.pattern == 1:
        return ChatConfigChangeProposalResponse(
            proposal_id=None,
            case_name=body.case_name,
            project_name=body.project_name,
            pattern=1,
            status="advisory",
            reason=body.reason,
            diff=[],
            proposed_changes=[],
            requires_approval=False,
            requires_confirmation=False,
            message="Advisory-only pattern: no configuration change proposal was persisted.",
        )

    try:
        proposed_config, diff = apply_changes_with_validation(base_config, changes_payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Patterns 2 and 3 are non-persistent proposal patterns.
    if body.pattern in {2, 3}:
        status = "draft" if body.pattern == 2 else "prefill"
        message = (
            "Draft-patch proposal created."
            if body.pattern == 2
            else "Form-prefill proposal created."
        )
        return ChatConfigChangeProposalResponse(
            proposal_id=None,
            case_name=body.case_name,
            project_name=body.project_name,
            pattern=body.pattern,
            status=status,
            reason=body.reason,
            diff=_as_diff_items(diff),
            proposed_changes=_as_change_items(changes_payload),
            requires_approval=False,
            requires_confirmation=False,
            message=message,
        )

    record = new_record(
        project_name=body.project_name,
        case_name=body.case_name,
        pattern=body.pattern,
        reason=body.reason,
        changes=changes_payload,
        base_config=base_config,
        proposed_config=proposed_config,
        diff=diff,
    )
    _chat_change_store.create(record)

    return ChatConfigChangeProposalResponse(
        proposal_id=record.proposal_id,
        case_name=record.case_name,
        project_name=record.project_name,
        pattern=record.pattern,
        status=record.status,
        reason=record.reason,
        diff=_as_diff_items(record.diff),
        proposed_changes=_as_change_items(record.changes),
        requires_approval=True,
        requires_confirmation=True,
        message="Proposal created. Explicit approval is required before apply.",
    )


@router.post("/config-changes/proposals/{proposal_id}/apply", response_model=ChatConfigChangeProposalResponse)
async def apply_chat_config_change_proposal(
    proposal_id: str,
    body: ChatConfigChangeApplyRequest,
) -> ChatConfigChangeProposalResponse:
    """Apply a proposal only after explicit user approval and revalidation."""
    if not body.approved_by_user:
        raise HTTPException(status_code=400, detail="approved_by_user must be true")

    try:
        record = _chat_change_store.get(proposal_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if record.case_name != body.case_name or record.project_name != body.project_name:
        raise HTTPException(status_code=409, detail="Proposal scope does not match the requested case/project.")
    if record.pattern not in {4, 5}:
        raise HTTPException(status_code=400, detail="Only pattern 4/5 proposals can be applied.")
    if record.status in TERMINAL_PROPOSAL_STATES:
        raise HTTPException(status_code=409, detail=f"Proposal is already {record.status}.")

    store = _get_store()
    try:
        latest_config = _ensure_case_exists(store, body.case_name, body.project_name)
    except CaseNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        applied_config, _ = apply_changes_with_validation(latest_config, deepcopy(record.changes))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        store.save(body.case_name, applied_config, project=body.project_name)
    except CaseNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _chat_change_store.update_status(proposal_id, "applied")

    return ChatConfigChangeProposalResponse(
        proposal_id=record.proposal_id,
        case_name=record.case_name,
        project_name=record.project_name,
        pattern=record.pattern,
        status="applied",
        reason=record.reason,
        diff=_as_diff_items(record.diff),
        proposed_changes=_as_change_items(record.changes),
        requires_approval=False,
        requires_confirmation=True,
        message="Proposal applied. Confirm after reviewing diff in UI.",
    )


@router.post("/config-changes/proposals/{proposal_id}/confirm", response_model=ChatConfigChangeProposalResponse)
async def confirm_chat_config_change_proposal(
    proposal_id: str,
    body: ChatConfigChangeConfirmRequest,
) -> ChatConfigChangeProposalResponse:
    """Finalize a previously applied proposal after UI diff confirmation."""
    if not body.confirmed_by_user:
        raise HTTPException(status_code=400, detail="confirmed_by_user must be true")

    try:
        record = _chat_change_store.get(proposal_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if record.case_name != body.case_name or record.project_name != body.project_name:
        raise HTTPException(status_code=409, detail="Proposal scope does not match the requested case/project.")
    if record.status != "applied":
        raise HTTPException(status_code=409, detail="Proposal must be in applied state before confirmation.")

    _chat_change_store.update_status(proposal_id, "confirmed")

    return ChatConfigChangeProposalResponse(
        proposal_id=record.proposal_id,
        case_name=record.case_name,
        project_name=record.project_name,
        pattern=record.pattern,
        status="confirmed",
        reason=record.reason,
        diff=_as_diff_items(record.diff),
        proposed_changes=_as_change_items(record.changes),
        requires_approval=False,
        requires_confirmation=False,
        message="Proposal confirmed.",
    )


@router.post("/config-changes/proposals/{proposal_id}/reject", response_model=ChatConfigChangeProposalResponse)
async def reject_chat_config_change_proposal(
    proposal_id: str,
    body: ChatConfigChangeRejectRequest,
) -> ChatConfigChangeProposalResponse:
    """Reject a proposal explicitly without persistence side effects."""
    if not body.rejected_by_user:
        raise HTTPException(status_code=400, detail="rejected_by_user must be true")

    try:
        record = _chat_change_store.get(proposal_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if record.case_name != body.case_name or record.project_name != body.project_name:
        raise HTTPException(status_code=409, detail="Proposal scope does not match the requested case/project.")
    if record.status in TERMINAL_PROPOSAL_STATES:
        raise HTTPException(status_code=409, detail=f"Proposal is already {record.status}.")

    _chat_change_store.update_status(proposal_id, "rejected")

    return ChatConfigChangeProposalResponse(
        proposal_id=record.proposal_id,
        case_name=record.case_name,
        project_name=record.project_name,
        pattern=record.pattern,
        status="rejected",
        reason=record.reason,
        diff=_as_diff_items(record.diff),
        proposed_changes=_as_change_items(record.changes),
        requires_approval=False,
        requires_confirmation=False,
        message="Proposal rejected.",
    )