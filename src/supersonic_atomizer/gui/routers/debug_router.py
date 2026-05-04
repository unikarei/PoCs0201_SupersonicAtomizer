from __future__ import annotations

from fastapi import APIRouter, Body
import logging

router = APIRouter()
logger = logging.getLogger("supersonic_atomizer.debug")


@router.post("/log")
async def post_log(message: str = Body(...), details: str | None = Body(None)) -> None:
    """Accept small client-side debug logs for investigation."""
    logger.warning("Client debug: %s -- %s", message, details)
    return None
