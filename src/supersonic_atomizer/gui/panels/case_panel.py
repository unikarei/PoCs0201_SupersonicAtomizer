"""Left panel — case management (P23-T04).

Renders the fixed left panel: case list, new-case creation, open-case loading.

Architectural boundary (architecture.md, Appendix B.3):
- This module may use ``case_store.py`` for persistence.
- It must not call the application service directly.
- All state mutations go through ``GUIState`` helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from supersonic_atomizer.gui.case_store import CaseStore, CaseNameError
from supersonic_atomizer.gui.state import GUIState


# ── Pure Python helpers (testable without Streamlit) ─────────────────────────


def populate_state_from_config(state: GUIState, config: dict[str, Any]) -> None:
    """Copy values from a raw config dict into the flat GUI state fields.

    Only known keys are copied; missing keys leave the corresponding state
    field at its current value (safe for partial configs).
    """
    fluid = config.get("fluid", {})
    bc = config.get("boundary_conditions", {})
    inj = config.get("droplet_injection", {})
    mdl = config.get("models", {})
    geo = config.get("geometry", {})

    if "working_fluid" in fluid:
        state.working_fluid = fluid["working_fluid"]
    if "inlet_wetness" in fluid:
        state.inlet_wetness = fluid["inlet_wetness"]

    if "Pt_in" in bc:
        state.inlet_total_pressure = float(bc["Pt_in"])
    if "Tt_in" in bc:
        state.inlet_total_temperature = float(bc["Tt_in"])
    if "Ps_out" in bc:
        state.outlet_static_pressure = float(bc["Ps_out"])

    if "droplet_velocity_in" in inj:
        state.droplet_velocity_in = float(inj["droplet_velocity_in"])
    if "droplet_diameter_mean_in" in inj:
        state.droplet_diameter_mean_in = float(inj["droplet_diameter_mean_in"])
    if "droplet_diameter_max_in" in inj:
        state.droplet_diameter_max_in = float(inj["droplet_diameter_max_in"])

    if "critical_weber_number" in mdl:
        state.critical_weber_number = float(mdl["critical_weber_number"])
    if "breakup_factor_mean" in mdl:
        state.breakup_factor_mean = float(mdl["breakup_factor_mean"])
    if "breakup_factor_max" in mdl:
        state.breakup_factor_max = float(mdl["breakup_factor_max"])

    if "x_start" in geo:
        state.x_start = float(geo["x_start"])
    if "x_end" in geo:
        state.x_end = float(geo["x_end"])
    if "n_cells" in geo:
        state.n_cells = int(geo["n_cells"])

    area_dist = geo.get("area_distribution", {})
    if area_dist.get("type") == "table":
        xs = area_dist.get("x", [])
        As = area_dist.get("A", [])
        if xs and As and len(xs) == len(As):
            state.area_table = [{"x": float(x), "A": float(a)} for x, a in zip(xs, As)]


def apply_case_selection(state: GUIState, name: str, store: CaseStore) -> None:
    """Load a case from the store and populate state.

    Raises
    ------
    CaseNotFoundError
        If the named case does not exist.
    """
    config = store.load(name)
    state.active_case_name = name
    state.active_case_path = str(store.case_path(name))
    # Reset run state when switching cases
    state.last_run_result = None
    state.solver_error = None
    populate_state_from_config(state, config)


def apply_new_case(state: GUIState, name: str, store: CaseStore) -> Path:
    """Create a new case in the store and set it as the active case.

    Returns the path to the newly created YAML file.

    Raises
    ------
    CaseNameError
        If the name is invalid.
    FileExistsError
        If a case with this name already exists.
    """
    path = store.create(name)
    state.active_case_name = name
    state.active_case_path = str(path)
    # Reset run state for the new case
    state.last_run_result = None
    state.solver_error = None
    return path


# ── Streamlit render function ────────────────────────────────────────────────


def render_case_panel() -> None:
    """Render the left case-management panel (requires Streamlit context)."""
    import streamlit as st

    state: GUIState = st.session_state.gui_state
    store = CaseStore()

    st.markdown("### Cases")

    case_names = store.list_cases()
    if case_names:
        selected = st.radio(
            "Select a case",
            options=case_names,
            index=case_names.index(state.active_case_name)
            if state.active_case_name in case_names
            else 0,
            key="case_radio",
        )
        if selected != state.active_case_name:
            try:
                apply_case_selection(state, selected, store)
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Failed to load case: {exc}")
    else:
        st.info("No cases yet. Create one below.")

    st.divider()

    with st.expander("➕ New Case", expanded=not bool(case_names)):
        new_name = st.text_input("Case name", key="new_case_name")
        if st.button("Create", key="btn_create_case"):
            if not new_name:
                st.error("Name cannot be empty.")
            else:
                try:
                    apply_new_case(state, new_name, store)
                    st.rerun()
                except CaseNameError as exc:
                    st.error(str(exc))
                except FileExistsError:
                    st.error(f"Case '{new_name}' already exists.")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Unexpected error: {exc}")

    if state.active_case_name:
        st.markdown(f"**Active:** `{state.active_case_name}`")
