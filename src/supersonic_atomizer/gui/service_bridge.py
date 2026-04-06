"""Thin adapter between GUI events and the application service boundary.

This module is the ONLY permitted call site into the application service
from the gui/ layer (architecture.md, Appendix B.3).

All other gui/ modules must obtain simulation results through this bridge
and must not import from app/, solvers/, thermo/, config/, or breakup/ directly.

Design notes
------------
Two execution paths are provided:

1. ``run_simulation_sync`` — synchronous, intended for tests and simple scripts.
2. ``run_simulation_async`` — background thread, intended for Streamlit callers.
   The caller provides ``on_complete`` and ``on_error`` callbacks.  In Streamlit,
   these callbacks update ``st.session_state`` and call ``st.rerun()``, but the
   bridge itself has no Streamlit dependency.

The thread returned by ``run_simulation_async`` is a daemon thread so it does not
prevent interpreter shutdown.  Callers can check ``thread.is_alive()`` to drive
a progress indicator.
"""

from __future__ import annotations

import threading
from typing import Callable

from supersonic_atomizer.app.services import (
    ApplicationService,
    SimulationRunResult,
    StartupResult,
    create_application_service,
)


class ServiceBridge:
    """Adapts GUI events to application-service calls.

    Parameters
    ----------
    service:
        The ``ApplicationService`` instance to delegate to.  When ``None``,
        the production default created by ``create_application_service()`` is used.
        Passing a mock service is the recommended approach for testing.
    """

    def __init__(self, service: ApplicationService | None = None) -> None:
        self._service: ApplicationService = service or create_application_service()

    @property
    def service(self) -> ApplicationService:
        """Expose the underlying service (read-only) for introspection in tests."""
        return self._service

    # ── Validation ──────────────────────────────────────────────────────────────

    def validate_case(self, case_path: str) -> StartupResult:
        """Run startup-only validation without executing the simulation.

        Useful for providing early feedback to the user before committing to a
        full run.  Returns a ``StartupResult`` with ``status="ready"`` on success
        or ``status="failed"`` with failure details on error.
        """
        return self._service.run_startup(case_path)

    # ── Synchronous execution (testing / scripting) ─────────────────────────────

    def run_simulation_sync(self, case_path: str) -> SimulationRunResult:
        """Invoke the full simulation synchronously and return the result.

        Intended for testing only.  GUI code should use ``run_simulation_async``
        to keep the UI responsive during long-running solves.
        """
        return self._service.run_simulation(case_path)

    # ── Asynchronous execution (GUI / Streamlit) ────────────────────────────────

    def run_simulation_async(
        self,
        case_path: str,
        on_complete: Callable[[SimulationRunResult], None],
        on_error: Callable[[Exception], None],
    ) -> threading.Thread:
        """Invoke the simulation in a background daemon thread.

        Parameters
        ----------
        case_path:
            Path to the YAML case file to simulate.
        on_complete:
            Called with the ``SimulationRunResult`` when the run finishes.
            In Streamlit callers this callback should update ``st.session_state``
            and call ``st.rerun()`` to refresh the UI.
        on_error:
            Called with the unexpected ``Exception`` if one escapes the
            application-service boundary.  The service itself converts known
            error categories into ``SimulationRunResult(status="failed")``,
            so ``on_error`` is only reached for truly unexpected failures.

        Returns
        -------
        threading.Thread
            The background thread.  Callers can call ``thread.is_alive()`` to
            drive a spinner or disable the Run button while the solver runs.
        """

        def _run() -> None:
            try:
                result = self._service.run_simulation(case_path)
                on_complete(result)
            except Exception as exc:  # noqa: BLE001
                on_error(exc)

        thread = threading.Thread(target=_run, daemon=True, name="solver-thread")
        thread.start()
        return thread
