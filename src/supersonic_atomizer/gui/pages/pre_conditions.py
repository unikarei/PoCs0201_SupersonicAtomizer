"""Pre Tab 1 — analysis conditions form (P23-T05).

Provides form controls for all required simulation inputs with inline SI unit
labels and validation.  All validation and state-conversion helpers are pure
Python so they can be tested without a Streamlit context.

Architectural boundary: no imports from solvers/, thermo/, config/, or breakup/.
"""

from __future__ import annotations

from typing import Any

from supersonic_atomizer.gui.state import GUIState

# Allowed working-fluid values (mirrors config schema)
SUPPORTED_FLUIDS = ("air", "steam")


# ── Validation helpers ────────────────────────────────────────────────────────


def validate_conditions(state: GUIState) -> list[str]:
    """Return a list of human-readable validation error messages.

    An empty list means all conditions are valid.
    """
    errors: list[str] = []

    if state.working_fluid not in SUPPORTED_FLUIDS:
        errors.append(
            f"Unsupported working fluid '{state.working_fluid}'. "
            f"Must be one of: {', '.join(SUPPORTED_FLUIDS)}."
        )

    if state.inlet_total_pressure <= 0:
        errors.append("Inlet total pressure (P₀) must be > 0 Pa.")

    if state.inlet_total_temperature <= 0:
        errors.append("Inlet total temperature (T₀) must be > 0 K.")

    if state.outlet_static_pressure <= 0:
        errors.append("Outlet static pressure (P₂) must be > 0 Pa.")

    if state.outlet_static_pressure >= state.inlet_total_pressure:
        errors.append(
            "Outlet static pressure (P₂) must be less than inlet total pressure (P₀) "
            "to drive subsonic flow."
        )

    if state.droplet_velocity_in <= 0:
        errors.append("Initial droplet velocity must be > 0 m/s.")

    if state.droplet_diameter_mean_in <= 0:
        errors.append("Initial mean droplet diameter must be > 0 m.")

    if state.droplet_diameter_max_in <= 0:
        errors.append("Initial maximum droplet diameter must be > 0 m.")

    if state.droplet_diameter_max_in < state.droplet_diameter_mean_in:
        errors.append(
            "Initial maximum droplet diameter must be ≥ mean diameter."
        )

    if state.critical_weber_number <= 0:
        errors.append("Critical Weber number must be > 0.")

    if not (0 < state.breakup_factor_mean < 1):
        errors.append("Breakup factor (mean) must be in (0, 1).")

    if not (0 < state.breakup_factor_max < 1):
        errors.append("Breakup factor (max) must be in (0, 1).")

    if state.working_fluid == "steam" and state.inlet_wetness is not None:
        if not (0.0 <= state.inlet_wetness < 1.0):
            errors.append("Inlet wetness must be in [0, 1) for steam cases.")

    return errors


# ── Config conversion helper ──────────────────────────────────────────────────


def state_to_conditions_config(state: GUIState) -> dict[str, Any]:
    """Convert condition-related GUI state fields to a config dict fragment.

    Returns a dict containing the ``fluid``, ``boundary_conditions``,
    ``droplet_injection``, and ``models`` sections — ready to be merged with
    the geometry section before saving.
    """
    fluid: dict[str, Any] = {"working_fluid": state.working_fluid}
    if state.working_fluid == "steam" and state.inlet_wetness is not None:
        fluid["inlet_wetness"] = state.inlet_wetness

    return {
        "fluid": fluid,
        "boundary_conditions": {
            "Pt_in": state.inlet_total_pressure,
            "Tt_in": state.inlet_total_temperature,
            "Ps_out": state.outlet_static_pressure,
        },
        "droplet_injection": {
            "droplet_velocity_in": state.droplet_velocity_in,
            "droplet_diameter_mean_in": state.droplet_diameter_mean_in,
            "droplet_diameter_max_in": state.droplet_diameter_max_in,
        },
        "models": {
            "breakup_model": "weber_critical",
            "critical_weber_number": state.critical_weber_number,
            "breakup_factor_mean": state.breakup_factor_mean,
            "breakup_factor_max": state.breakup_factor_max,
        },
    }


# ── Streamlit render function ────────────────────────────────────────────────


def render_pre_conditions() -> None:
    """Render the Pre Tab 1 analysis-conditions form (requires Streamlit context)."""
    import streamlit as st

    state: GUIState = st.session_state.gui_state

    if state.active_case_name is None:
        st.info("Create or open a case in the left panel first.")
        return

    st.subheader("Analysis Conditions")

    # Working fluid
    fluid_index = list(SUPPORTED_FLUIDS).index(state.working_fluid) if state.working_fluid in SUPPORTED_FLUIDS else 0
    state.working_fluid = st.selectbox("Working fluid", options=SUPPORTED_FLUIDS, index=fluid_index)

    # Boundary conditions
    st.markdown("**Boundary Conditions**")
    state.inlet_total_pressure = st.number_input(
        "Inlet total pressure P₀ (Pa)", value=state.inlet_total_pressure, min_value=0.0, step=1000.0
    )
    state.inlet_total_temperature = st.number_input(
        "Inlet total temperature T₀ (K)", value=state.inlet_total_temperature, min_value=0.0, step=1.0
    )
    state.outlet_static_pressure = st.number_input(
        "Outlet static pressure P₂ (Pa)", value=state.outlet_static_pressure, min_value=0.0, step=1000.0
    )

    if state.working_fluid == "steam":
        wetness_val = state.inlet_wetness if state.inlet_wetness is not None else 0.0
        state.inlet_wetness = st.number_input(
            "Inlet wetness (dimensionless)", value=wetness_val, min_value=0.0, max_value=0.999, step=0.01
        )
    else:
        state.inlet_wetness = None

    # Droplet injection
    st.markdown("**Droplet Injection**")
    state.droplet_velocity_in = st.number_input(
        "Initial droplet velocity (m/s)", value=state.droplet_velocity_in, min_value=0.0, step=0.1
    )
    state.droplet_diameter_mean_in = st.number_input(
        "Initial mean diameter (m)", value=state.droplet_diameter_mean_in, min_value=0.0, format="%.2e"
    )
    state.droplet_diameter_max_in = st.number_input(
        "Initial max diameter (m)", value=state.droplet_diameter_max_in, min_value=0.0, format="%.2e"
    )

    # Breakup parameters
    st.markdown("**Breakup Model**")
    state.critical_weber_number = st.number_input(
        "Critical Weber number", value=state.critical_weber_number, min_value=0.0, step=0.5
    )
    state.breakup_factor_mean = st.number_input(
        "Breakup factor (mean)", value=state.breakup_factor_mean, min_value=0.01, max_value=0.99, step=0.05
    )
    state.breakup_factor_max = st.number_input(
        "Breakup factor (max)", value=state.breakup_factor_max, min_value=0.01, max_value=0.99, step=0.05
    )

    # Inline validation
    errors = validate_conditions(state)
    if errors:
        for err in errors:
            st.error(err)
    else:
        st.success("Conditions valid ✓")
