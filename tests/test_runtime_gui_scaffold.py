"""Tests: P23-T02 — GUI package scaffold import wiring.

Verifies that every module documented in architecture.md Appendix B.2 can
be imported without error and exports the expected public symbols.
"""

from __future__ import annotations

import importlib

import pytest


# ── All documented gui modules ─────────────────────────────────────────────────

GUI_MODULES = [
    "supersonic_atomizer.gui",
    "supersonic_atomizer.gui.state",
    "supersonic_atomizer.gui.service_bridge",
    "supersonic_atomizer.gui.case_store",
    "supersonic_atomizer.gui.app",
    "supersonic_atomizer.gui.layout",
    "supersonic_atomizer.gui.panels",
    "supersonic_atomizer.gui.panels.case_panel",
    "supersonic_atomizer.gui.pages",
    "supersonic_atomizer.gui.pages.pre_conditions",
    "supersonic_atomizer.gui.pages.pre_grid",
    "supersonic_atomizer.gui.pages.solve",
    "supersonic_atomizer.gui.pages.post_graphs",
    "supersonic_atomizer.gui.pages.post_table",
]


@pytest.mark.parametrize("module_path", GUI_MODULES)
def test_gui_module_importable(module_path: str) -> None:
    """Every documented GUI module must be importable."""
    module = importlib.import_module(module_path)
    assert module is not None


# ── Core symbol exports ────────────────────────────────────────────────────────


def test_gui_state_class_exported() -> None:
    from supersonic_atomizer.gui.state import GUIState

    assert GUIState is not None


def test_service_bridge_class_exported() -> None:
    from supersonic_atomizer.gui.service_bridge import ServiceBridge

    assert ServiceBridge is not None


def test_case_store_class_exported() -> None:
    from supersonic_atomizer.gui.case_store import CaseStore

    assert CaseStore is not None


def test_stub_modules_export_render_functions() -> None:
    """Stub page/panel modules must export their documented render functions."""
    from supersonic_atomizer.gui.app import run_gui
    from supersonic_atomizer.gui.layout import render_layout
    from supersonic_atomizer.gui.panels.case_panel import render_case_panel
    from supersonic_atomizer.gui.pages.post_graphs import render_post_graphs
    from supersonic_atomizer.gui.pages.post_table import render_post_table
    from supersonic_atomizer.gui.pages.pre_conditions import render_pre_conditions
    from supersonic_atomizer.gui.pages.pre_grid import render_pre_grid
    from supersonic_atomizer.gui.pages.solve import render_solve

    for fn in (
        run_gui,
        render_layout,
        render_case_panel,
        render_pre_conditions,
        render_pre_grid,
        render_solve,
        render_post_graphs,
        render_post_table,
    ):
        assert callable(fn)


# ── GUIState construction ──────────────────────────────────────────────────────


def test_gui_state_default_construction() -> None:
    from supersonic_atomizer.gui.state import GUIState

    state = GUIState()
    assert state.working_fluid == "air"
    assert state.solver_running is False
    assert state.last_run_result is None
    assert state.solver_error is None
    assert state.active_case_name is None


def test_gui_state_area_table_default_nonempty() -> None:
    from supersonic_atomizer.gui.state import GUIState

    state = GUIState()
    assert len(state.area_table) > 0
    for row in state.area_table:
        assert "x" in row
        assert "A" in row
        assert row["A"] > 0.0


def test_gui_state_mark_running() -> None:
    from supersonic_atomizer.gui.state import GUIState

    state = GUIState()
    state.solver_error = "previous error"
    state.mark_running()
    assert state.solver_running is True
    assert state.last_run_result is None
    assert state.solver_error is None


def test_gui_state_mark_error() -> None:
    from supersonic_atomizer.gui.state import GUIState

    state = GUIState()
    state.solver_running = True
    state.mark_error("boom")
    assert state.solver_running is False
    assert state.solver_error == "boom"


def test_gui_state_mark_complete() -> None:
    from supersonic_atomizer.app.services import SimulationRunResult
    from supersonic_atomizer.gui.state import GUIState

    state = GUIState()
    state.solver_running = True
    result = SimulationRunResult(status="completed", case_path="test.yaml")
    state.mark_complete(result)
    assert state.solver_running is False
    assert state.last_run_result is result


def test_gui_state_has_result_and_result_is_success() -> None:
    from supersonic_atomizer.app.services import SimulationRunResult
    from supersonic_atomizer.gui.state import GUIState

    state = GUIState()
    assert not state.has_result()
    assert not state.result_is_success()

    state.last_run_result = SimulationRunResult(status="completed", case_path="x")
    assert state.has_result()
    assert state.result_is_success()

    state.last_run_result = SimulationRunResult(status="failed", case_path="x")
    assert state.has_result()
    assert not state.result_is_success()
