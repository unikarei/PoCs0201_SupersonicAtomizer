"""Server-side session store for the FastAPI GUI layer (P25-T03).

Each browser session is identified by a UUID stored in a ``session_id``
cookie.  The server maintains one ``GUIState`` instance per session in an
in-memory dict.

This is a single-user / PoC implementation.  A production system would
use Redis or a database-backed session store.  Thread-safety is ensured
by a per-store ``threading.Lock``.
"""

from __future__ import annotations

import threading
import uuid
from typing import Optional

from supersonic_atomizer.gui.state import GUIState


class SessionStore:
    """Thread-safe in-memory store for GUI session state."""

    def __init__(self) -> None:
        self._sessions: dict[str, GUIState] = {}
        self._lock = threading.Lock()

    @staticmethod
    def new_session_id() -> str:
        """Generate a fresh session identifier."""
        return str(uuid.uuid4())

    def get_or_create(self, session_id: str) -> GUIState:
        """Return the GUIState for *session_id*, creating one if absent."""
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = GUIState()
            return self._sessions[session_id]

    def get(self, session_id: str) -> Optional[GUIState]:
        """Return the GUIState for *session_id* or ``None`` if not found."""
        with self._lock:
            return self._sessions.get(session_id)

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)


# Module-level singleton.
_session_store = SessionStore()


def get_session_store() -> SessionStore:
    """Return the module-level SessionStore singleton."""
    return _session_store
