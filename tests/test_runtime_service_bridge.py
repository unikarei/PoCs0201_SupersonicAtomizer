"""Tests: P23-T02 — ServiceBridge call delegation.

Verifies that ServiceBridge correctly wraps ApplicationService,
delegates all calls to the underlying service, and provides both
synchronous and asynchronous execution paths.
"""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock

import pytest

from supersonic_atomizer.app.services import (
    ApplicationService,
    SimulationRunResult,
    StartupResult,
)
from supersonic_atomizer.gui.service_bridge import ServiceBridge


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_mock_service(
    run_status: str = "completed",
    startup_status: str = "ready",
) -> MagicMock:
    """Return a mock ApplicationService with preset return values."""
    service = MagicMock(spec=ApplicationService)
    service.run_simulation.return_value = SimulationRunResult(
        status=run_status,
        case_path="mock.yaml",
    )
    service.run_startup.return_value = StartupResult(
        status=startup_status,
        case_path="mock.yaml",
    )
    return service


# ── Initialisation ─────────────────────────────────────────────────────────────


class TestServiceBridgeInit:
    def test_wraps_provided_service(self) -> None:
        service = _make_mock_service()
        bridge = ServiceBridge(service=service)
        assert bridge.service is service

    def test_creates_default_service_when_none(self) -> None:
        """ServiceBridge() with no argument must not raise."""
        bridge = ServiceBridge()
        assert bridge.service is not None

    def test_service_property_is_read_only_type(self) -> None:
        service = _make_mock_service()
        bridge = ServiceBridge(service=service)
        # property returns the same object each time
        assert bridge.service is bridge.service


# ── Synchronous path ───────────────────────────────────────────────────────────


class TestServiceBridgeSync:
    def test_run_simulation_sync_delegates_to_service(self) -> None:
        service = _make_mock_service()
        bridge = ServiceBridge(service=service)

        result = bridge.run_simulation_sync("case.yaml")

        service.run_simulation.assert_called_once_with("case.yaml")
        assert result.status == "completed"
        assert result.case_path == "mock.yaml"

    def test_validate_case_delegates_to_run_startup(self) -> None:
        service = _make_mock_service()
        bridge = ServiceBridge(service=service)

        result = bridge.validate_case("case.yaml")

        service.run_startup.assert_called_once_with("case.yaml")
        assert result.status == "ready"

    def test_run_simulation_sync_propagates_failed_status(self) -> None:
        service = _make_mock_service(run_status="failed")
        bridge = ServiceBridge(service=service)

        result = bridge.run_simulation_sync("case.yaml")
        assert result.status == "failed"

    def test_validate_case_propagates_failed_startup(self) -> None:
        service = _make_mock_service(startup_status="failed")
        bridge = ServiceBridge(service=service)

        result = bridge.validate_case("case.yaml")
        assert result.status == "failed"


# ── Asynchronous path ──────────────────────────────────────────────────────────


class TestServiceBridgeAsync:
    def test_run_simulation_async_returns_thread(self) -> None:
        service = _make_mock_service()
        bridge = ServiceBridge(service=service)

        thread = bridge.run_simulation_async(
            "case.yaml", lambda r: None, lambda e: None
        )
        assert isinstance(thread, threading.Thread)
        thread.join(timeout=5.0)

    def test_run_simulation_async_thread_is_daemon(self) -> None:
        service = _make_mock_service()
        bridge = ServiceBridge(service=service)

        thread = bridge.run_simulation_async(
            "case.yaml", lambda r: None, lambda e: None
        )
        assert thread.daemon is True
        thread.join(timeout=5.0)

    def test_run_simulation_async_invokes_on_complete(self) -> None:
        service = _make_mock_service()
        bridge = ServiceBridge(service=service)
        results: list[SimulationRunResult] = []

        thread = bridge.run_simulation_async(
            "case.yaml",
            on_complete=results.append,
            on_error=lambda e: (_ for _ in ()).throw(e),
        )
        thread.join(timeout=5.0)

        assert not thread.is_alive()
        assert len(results) == 1
        assert results[0].status == "completed"
        service.run_simulation.assert_called_once_with("case.yaml")

    def test_run_simulation_async_invokes_on_error_on_unexpected_exception(
        self,
    ) -> None:
        service = MagicMock(spec=ApplicationService)
        service.run_simulation.side_effect = RuntimeError("unexpected solver crash")
        bridge = ServiceBridge(service=service)
        errors: list[str] = []

        thread = bridge.run_simulation_async(
            "case.yaml",
            on_complete=lambda r: None,
            on_error=lambda e: errors.append(str(e)),
        )
        thread.join(timeout=5.0)

        assert not thread.is_alive()
        assert len(errors) == 1
        assert "unexpected solver crash" in errors[0]

    def test_run_simulation_async_on_complete_receives_failed_result(self) -> None:
        """A service-level failure is surfaced as a result, not as on_error."""
        service = _make_mock_service(run_status="failed")
        bridge = ServiceBridge(service=service)
        results: list[SimulationRunResult] = []
        errors: list[Exception] = []

        thread = bridge.run_simulation_async(
            "case.yaml",
            on_complete=results.append,
            on_error=errors.append,
        )
        thread.join(timeout=5.0)

        # The service converts known errors into SimulationRunResult(status="failed")
        # so on_complete should be called, not on_error.
        assert len(results) == 1
        assert results[0].status == "failed"
        assert len(errors) == 0

    def test_multiple_async_runs_are_independent(self) -> None:
        service = _make_mock_service()
        bridge = ServiceBridge(service=service)
        results: list[SimulationRunResult] = []

        threads = [
            bridge.run_simulation_async(
                f"case_{i}.yaml",
                on_complete=results.append,
                on_error=lambda e: None,
            )
            for i in range(3)
        ]
        for t in threads:
            t.join(timeout=5.0)

        assert service.run_simulation.call_count == 3
        assert len(results) == 3
