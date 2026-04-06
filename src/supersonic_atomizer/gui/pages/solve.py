"""Solve tab — run control and convergence display (P23-T07)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from supersonic_atomizer.gui.case_store import CaseStore
from supersonic_atomizer.gui.pages.pre_conditions import state_to_conditions_config, validate_conditions
from supersonic_atomizer.gui.pages.pre_grid import state_to_geometry_config, validate_area_table
from supersonic_atomizer.gui.service_bridge import ServiceBridge
from supersonic_atomizer.gui.state import GUIState


def build_case_config_from_state(state: GUIState) -> dict[str, Any]:
    """Build a full raw case-config dict from GUI state."""
    config = {}
    config.update(state_to_conditions_config(state))
    config.update(state_to_geometry_config(state))
    config["outputs"] = {
        "output_directory": f"outputs/{state.active_case_name or 'gui_case'}",
        "write_csv": True,
        "write_json": True,
        "generate_plots": True,
    }
    return config


def validate_ready_to_run(state: GUIState) -> list[str]:
    """Aggregate all pre-run validation errors."""
    errors = []
    errors.extend(validate_conditions(state))
    errors.extend(validate_area_table(state.area_table))
    if state.active_case_name is None:
        errors.append("No active case selected.")
    if state.x_end <= state.x_start:
        errors.append("x end must be greater than x start.")
    return errors


def persist_state_to_case(state: GUIState, store: CaseStore) -> Path:
    """Save current GUI state into the active case YAML file and return its path."""
    if state.active_case_name is None:
        raise ValueError("No active case selected.")
    config = build_case_config_from_state(state)
    return store.save(state.active_case_name, config)


def render_solve() -> None:
    """Render the Solve tab with run controls and status display."""
    import streamlit as st

    state: GUIState = st.session_state.gui_state
    store = CaseStore()
    bridge = ServiceBridge()

    st.subheader("Solve")
    st.caption("The solver runs in a background thread. The Run button is disabled while a run is active.")

    errors = validate_ready_to_run(state)
    if errors:
        for err in errors:
            st.error(err)
    else:
        st.success("Ready to run ✓")

    def _on_complete(result):
        state.mark_complete(result)

    def _on_error(exc: Exception):
        state.mark_error(str(exc))

    run_disabled = state.solver_running or bool(errors)
    if st.button("Run", disabled=run_disabled):
        try:
            case_path = persist_state_to_case(state, store)
            state.mark_running()
            bridge.run_simulation_async(str(case_path), on_complete=_on_complete, on_error=_on_error)
            st.info("Simulation started.")
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            state.mark_error(str(exc))
            st.error(f"Failed to start simulation: {exc}")

    if state.solver_running:
        st.warning("Simulation is running...")

    if state.solver_error:
        st.error(f"Solver error: {state.solver_error}")

    if state.last_run_result is not None:
        result = state.last_run_result
        if result.status == "completed":
            st.success("Simulation completed successfully.")
        elif result.status == "output-failed":
            st.warning(f"Simulation completed but output generation failed: {result.failure_message}")
        else:
            st.error(f"Simulation failed at stage '{result.failure_stage}': {result.failure_message}")

        # MVP has no iteration-based convergence history yet; show status placeholder.
        st.markdown("**Convergence history**")
        st.info("No iterative convergence history is available in the current solver implementation.")

