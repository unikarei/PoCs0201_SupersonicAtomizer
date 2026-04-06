"""Unit settings page — display unit selection (P24-T04).

Provides pure-Python helpers for unit-preference management and a Streamlit
render function for the ⚙ Settings tab.

Architectural boundary (architecture.md, Appendix B.9):
- This module calls only gui/unit_settings.py and GUIState helpers.
- It must not import from solvers/, thermo/, config/, breakup/, or app/.
- All Pre-tab inputs remain in SI units; only Post-tab display is affected.
"""

from __future__ import annotations

from supersonic_atomizer.gui.state import GUIState
from supersonic_atomizer.gui.unit_settings import DEFAULT_UNITS, UNIT_GROUPS


# Human-readable label for each unit group shown in the settings page.
UNIT_GROUP_LABELS: dict[str, str] = {
    "pressure":    "Pressure",
    "temperature": "Temperature",
    "velocity":    "Velocity",
    "diameter":    "Droplet diameter",
    "length":      "Axial position (x)",
    "area":        "Cross-section area",
    "density":     "Density",
}

# Maps each group name to the corresponding GUIState field name.
_STATE_FIELD: dict[str, str] = {
    "pressure":    "unit_pressure",
    "temperature": "unit_temperature",
    "velocity":    "unit_velocity",
    "diameter":    "unit_diameter",
    "length":      "unit_length",
    "area":        "unit_area",
    "density":     "unit_density",
}


# ── Pure helpers (testable without Streamlit) ─────────────────────────────────


def get_unit_choices(group: str) -> list[str]:
    """Return the list of available unit labels for *group*.

    Parameters
    ----------
    group:
        Unit group key, e.g. ``"pressure"``.

    Raises
    ------
    KeyError
        If *group* is not in UNIT_GROUPS.
    """
    return list(UNIT_GROUPS[group].keys())


def apply_unit_preference(state: GUIState, group: str, unit_label: str) -> None:
    """Set the display unit for *group* on the GUI state.

    Parameters
    ----------
    state:
        Mutable GUI session state.
    group:
        Unit group key.
    unit_label:
        A unit label that must exist in ``UNIT_GROUPS[group]``.

    Raises
    ------
    KeyError
        If *group* or *unit_label* is unknown.
    ValueError
        If *group* has no corresponding state field.
    """
    if group not in UNIT_GROUPS:
        raise KeyError(f"Unknown unit group: {group!r}")
    if unit_label not in UNIT_GROUPS[group]:
        raise KeyError(f"Unknown unit {unit_label!r} for group {group!r}")
    field = _STATE_FIELD.get(group)
    if field is None:
        raise ValueError(f"No GUIState field mapped for group {group!r}")
    setattr(state, field, unit_label)


def get_unit_preference(state: GUIState, group: str) -> str:
    """Return the currently selected display unit for *group* from *state*.

    Falls back to :data:`DEFAULT_UNITS` if the field is absent.

    Parameters
    ----------
    state:
        GUI session state.
    group:
        Unit group key.
    """
    field = _STATE_FIELD.get(group)
    if field is None:
        return DEFAULT_UNITS.get(group, "")
    return getattr(state, field, DEFAULT_UNITS.get(group, ""))


# ── Streamlit render ──────────────────────────────────────────────────────────


def render_unit_settings() -> None:
    """Render the ⚙ Settings tab with per-group unit selectboxes."""
    import streamlit as st

    state: GUIState = st.session_state.gui_state

    st.subheader("⚙ Display Units")
    st.caption(
        "These settings affect only what is displayed in the Post tabs. "
        "All solver inputs and outputs remain in SI units internally."
    )

    st.divider()

    changed = False
    for group, label in UNIT_GROUP_LABELS.items():
        choices = get_unit_choices(group)
        current = get_unit_preference(state, group)
        idx = choices.index(current) if current in choices else 0
        selected = st.selectbox(label, choices, index=idx, key=f"unit_pref_{group}")
        if selected != current:
            apply_unit_preference(state, group, selected)
            changed = True

    if changed:
        st.rerun()

    st.divider()
    st.info(
        "**Pre-tab inputs** are always accepted in SI units (Pa, K, m, m/s). "
        "Unit preferences apply only to the **Post — Graphs** and **Post — Table** displays."
    )
