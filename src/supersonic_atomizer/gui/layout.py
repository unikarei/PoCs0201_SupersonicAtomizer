"""Top-level layout composition (P23-T10, updated P24-T06)."""

from __future__ import annotations

from supersonic_atomizer.gui.panels.case_panel import render_case_panel
from supersonic_atomizer.gui.pages.post_graphs import render_post_graphs
from supersonic_atomizer.gui.pages.post_table import render_post_table
from supersonic_atomizer.gui.pages.pre_conditions import render_pre_conditions
from supersonic_atomizer.gui.pages.pre_grid import render_pre_grid
from supersonic_atomizer.gui.pages.solve import render_solve
from supersonic_atomizer.gui.pages.unit_settings_page import render_unit_settings


def render_layout() -> None:
    """Render the documented left-panel + main-area tab layout."""
    import streamlit as st

    left_col, main_col = st.columns([1, 3])

    with left_col:
        render_case_panel()

    with main_col:
        pre_tab, solve_tab, post_graphs_tab, post_table_tab, settings_tab = st.tabs(
            ["Pre — Conditions", "Solve", "Post — Graphs", "Post — Table", "⚙ Settings"]
        )
        with pre_tab:
            render_pre_conditions()
            st.divider()
            render_pre_grid()
        with solve_tab:
            render_solve()
        with post_graphs_tab:
            render_post_graphs()
        with post_table_tab:
            render_post_table()
        with settings_tab:
            render_unit_settings()

