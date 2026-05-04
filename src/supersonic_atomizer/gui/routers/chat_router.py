"""Case-aware chat endpoints for the FastAPI GUI (P34-T05)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from supersonic_atomizer.gui.case_store import CaseNameError, CaseNotFoundError, CaseStore
from supersonic_atomizer.gui.chat_service import ChatConfigurationError, ChatService
from supersonic_atomizer.gui.schemas import ChatReplyResponse, ChatRequest, ChatMessage

router = APIRouter()
_chat_service = ChatService()


def _get_store() -> CaseStore:
    return CaseStore()


@router.post("/messages", response_model=ChatReplyResponse)
async def send_chat_message(request: Request, body: ChatRequest) -> ChatReplyResponse:
    """Return a case-aware assistant reply for the selected case."""
    store = _get_store()
    try:
        if not store.exists(body.case_name, project=body.project_name):
            raise HTTPException(status_code=404, detail=f"Case {body.case_name!r} not found.")
        case_config = store.load(body.case_name, project=body.project_name)
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CaseNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Allow optional per-request model override via X-LLM-MODEL header
    model_override = None
    try:
        model_override = request.headers.get("X-LLM-MODEL")
    except Exception:
        model_override = None

    try:
        reply_text = _chat_service.generate_reply(
            project_name=body.project_name,
            case_name=body.case_name,
            case_config=case_config,
            messages=[{"role": message.role, "content": message.content} for message in body.messages],
            model_override=model_override,
        )
    except ChatConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ChatReplyResponse(reply=ChatMessage(role="assistant", content=reply_text))