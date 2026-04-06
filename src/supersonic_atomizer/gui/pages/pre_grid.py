"""Pre Tab 2 — grid definition and area preview (P23-T06)."""

from __future__ import annotations

from typing import Any

from supersonic_atomizer.gui.state import GUIState


def validate_area_table(area_table: list[dict[str, Any]]) -> list[str]:
    """Validate the editable (x, A) table and return human-readable errors."""
    errors: list[str] = []
    if len(area_table) < 2:
        errors.append("Area table must contain at least two rows.")
        return errors

    x_values = []
    for index, row in enumerate(area_table):
        if "x" not in row or "A" not in row:
            errors.append(f"Row {index + 1} must contain both 'x' and 'A'.")
            continue
        x_value = row["x"]
        area_value = row["A"]
        try:
            x_float = float(x_value)
            area_float = float(area_value)
        except (TypeError, ValueError):
            errors.append(f"Row {index + 1} contains non-numeric values.")
            continue
        if area_float <= 0:
            errors.append(f"Row {index + 1} has nonpositive area.")
        x_values.append(x_float)

    if any(x2 <= x1 for x1, x2 in zip(x_values, x_values[1:])):
        errors.append("Area-table x values must be strictly increasing.")

    return errors


def state_to_geometry_config(state: GUIState) -> dict[str, Any]:
    """Convert grid-related GUI state to the geometry config fragment."""
    x_values = [float(row["x"]) for row in state.area_table]
    area_values = [float(row["A"]) for row in state.area_table]
    return {
        "geometry": {
            "x_start": state.x_start,
            "x_end": state.x_end,
            "n_cells": state.n_cells,
            "area_distribution": {
                "type": "table",
                "x": x_values,
                "A": area_values,
            },
        }
    }


def render_pre_grid() -> None:
    """Render the Pre Tab 2 grid-definition table and area preview."""
    import pandas as pd
    import streamlit as st
    import matplotlib.pyplot as plt

    state: GUIState = st.session_state.gui_state

    if state.active_case_name is None:
        st.info("Create or open a case in the left panel first.")
        return

    st.subheader("Grid Definition")
    state.x_start = st.number_input("x start (m)", value=state.x_start, step=0.01)
    state.x_end = st.number_input("x end (m)", value=state.x_end, step=0.01)
    state.n_cells = int(st.number_input("Cell count", value=state.n_cells, min_value=2, step=1))

    st.markdown("**Area distribution table (x, A)**")
    df = pd.DataFrame(state.area_table)
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="area_table_editor")
    state.area_table = edited.to_dict(orient="records")

    errors = validate_area_table(state.area_table)
    if state.x_end <= state.x_start:
        errors.append("x end must be greater than x start.")

    if errors:
        for err in errors:
            st.error(err)
        return

    st.success("Grid valid ✓")

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot([row["x"] for row in state.area_table], [row["A"] for row in state.area_table], marker="o")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("A (m²)")
    ax.set_title("Area profile preview")
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

