"""FastAPI dependency-injection helpers for the GUI layer (P25-T03).

These helpers are used with ``Depends()`` in route handlers so that
session-state resolution stays out of router business logic.

Session identification
----------------------
The browser receives a ``session_id`` UUID cookie on first visit (set by
``index_router``).  Subsequent requests carry the cookie automatically.
The dependency ``get_session_id`` reads it; ``get_gui_state`` resolves the
associated ``GUIState`` from the session store.
"""

from __future__ import annotations

import uuid

from fastapi import Cookie, Response

from supersonic_atomizer.gui.session_store import get_session_store
from supersonic_atomizer.gui.state import GUIState


def get_or_create_session_id(
    response: Response,
    session_id: str | None = Cookie(default=None),
) -> str:
    """Return the current session id, setting a fresh cookie when absent."""
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            samesite="lax",
        )
    return session_id


def get_gui_state(
    response: Response,
    session_id: str | None = Cookie(default=None),
) -> GUIState:
    """Resolve ``GUIState`` for the current browser session.

    Creates a new session (and cookie) when none exists.
    """
    sid = get_or_create_session_id(response, session_id)
    return get_session_store().get_or_create(sid)
