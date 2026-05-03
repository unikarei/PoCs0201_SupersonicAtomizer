"""Post Tab 1 — axial profile plots (P23-T08, updated P24-T05)."""

from __future__ import annotations

from typing import Any

from supersonic_atomizer.domain import SimulationResult
from supersonic_atomizer.gui.unit_settings import (
    DEFAULT_UNITS,
    convert_series,
    display_unit_label,
)


PLOT_FIELDS: dict[str, tuple[str, str, str]] = {
    "area_profile":           ("Area Profile",          "area",       "m²"),
    "pressure":               ("Pressure",               "pressure",   "Pa"),
    "temperature":            ("Temperature",            "temperature", "K"),
    "working_fluid_velocity": ("Working-fluid velocity", "velocity",   "m/s"),
    "droplet_velocity":       ("Droplet velocity",       "velocity",   "m/s"),
    "slip_velocity":          ("Slip velocity",          "velocity",   "m/s"),
    "Mach_number":            ("Mach number",            None,         "-"),
    "droplet_mean_diameter":  ("Droplet mean diameter",  "diameter",   "m"),
    "droplet_maximum_diameter": ("Droplet maximum diameter", "diameter", "m"),
    "Weber_number":           ("Weber number",           None,         "-"),
    "pressure_over_total":    ("Pressure / inlet total pressure", None,   "-"),
}


def extract_plot_series(
    simulation_result: SimulationResult,
    unit_preferences: dict[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Extract plot-ready axial series from a SimulationResult.

    Parameters
    ----------
    simulation_result:
        The completed simulation result.
    unit_preferences:
        Optional mapping of unit-group name to display unit label (from
        ``GUIState.unit_preferences()``).  When ``None`` all values are
        returned in SI units with SI axis labels — preserving backward
        compatibility with existing tests.
    """

    def _convert(si_values: list[float], group: str | None) -> tuple[list[float], str]:
        """Return (display_values, unit_label)."""
        if group is None:
            return list(si_values), "-"
        if unit_preferences is not None:
            return (
                convert_series(list(si_values), group, unit_preferences),
                display_unit_label(group, unit_preferences),
            )
        return list(si_values), DEFAULT_UNITS.get(group, "")

    x_si = list(simulation_result.gas_solution.x_values)
    x_disp, x_unit = _convert(x_si, "length")
    x_label = f"x ({x_unit})"

    def _entry(si_values, group: str | None, title: str) -> dict[str, Any]:
        y, unit = _convert(list(si_values), group)
        ylabel = f"{title} ({unit})" if unit != "-" else f"{title} (-)"
        return {"x": x_disp, "y": y, "ylabel": ylabel, "title": title, "x_label": x_label}

    result = {
        "area_profile":         _entry(simulation_result.gas_solution.area_values,                         "area",        "Area Profile"),
        "pressure":               _entry(simulation_result.gas_solution.pressure_values,                          "pressure",    "Pressure"),
        "temperature":            _entry(simulation_result.gas_solution.temperature_values,                       "temperature", "Temperature"),
        "working_fluid_velocity": _entry(simulation_result.gas_solution.velocity_values,                          "velocity",    "Working-fluid velocity"),
        "droplet_velocity":       _entry(simulation_result.droplet_solution.velocity_values,                      "velocity",    "Droplet velocity"),
        "slip_velocity":          _entry(simulation_result.droplet_solution.slip_velocity_values,                 "velocity",    "Slip velocity"),
        "Mach_number":            _entry(simulation_result.gas_solution.mach_number_values,                       None,          "Mach number"),
        "droplet_mean_diameter":  _entry(simulation_result.droplet_solution.mean_diameter_values,                 "diameter",    "Droplet mean diameter"),
        "droplet_maximum_diameter": _entry(simulation_result.droplet_solution.maximum_diameter_values,            "diameter",    "Droplet maximum diameter"),
        "Weber_number":           _entry(simulation_result.droplet_solution.weber_number_values,                  None,          "Weber number"),
    }

    # Optionally include pressure normalized by inlet total pressure when
    # the run produced boundary-condition metadata. Older unit tests expect
    # this field to be omitted when settings_summary is empty, so only add
    # it when a Pt_in value is available.
    pt_in = simulation_result.settings_summary.get("boundary_conditions", {}).get("Pt_in") if simulation_result.settings_summary else None
    if pt_in is not None:
        result["pressure_over_total"] = _entry(
            [p / float(pt_in) for p in simulation_result.gas_solution.pressure_values],
            None,
            "Pressure / Inlet total pressure",
        )

    return result


def extract_overlay_plot_series(
    labeled_results: list[tuple[str, SimulationResult]] | tuple[tuple[str, SimulationResult], ...],
    unit_preferences: dict[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Extract per-field overlay data for multiple simulation results."""
    overlay: dict[str, dict[str, Any]] = {}
    for run_label, simulation_result in labeled_results:
        per_run_series = extract_plot_series(simulation_result, unit_preferences)
        for field, data in per_run_series.items():
            field_overlay = overlay.setdefault(
                field,
                {
                    "title": data["title"],
                    "x_label": data["x_label"],
                    "ylabel": data["ylabel"],
                    "series": [],
                },
            )
            field_overlay["series"].append(
                {
                    "label": run_label,
                    "x": data["x"],
                    "y": data["y"],
                }
            )
    return overlay


def render_post_graphs() -> None:
    """Render the Post Tab 1 axial profile plots with user-selected display units."""
    import io

    import matplotlib.pyplot as plt
    import streamlit as st

    state = st.session_state.gui_state
    if state.last_run_result is None or state.last_run_result.simulation_result is None:
        st.info("Run a simulation to display plots.")
        return

    result = state.last_run_result.simulation_result
    prefs = state.unit_preferences()
    series = extract_plot_series(result, prefs)

    selected = st.multiselect(
        "Quantities to display",
        options=list(PLOT_FIELDS.keys()),
        default=list(PLOT_FIELDS.keys()),
    )

    for key in selected:
        data = series[key]
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(data["x"], data["y"])
        ax.set_xlabel(data["x_label"])
        ax.set_ylabel(data["ylabel"])
        ax.set_title(data["title"])
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", bbox_inches="tight")
        st.download_button(
            label=f"Export {key} as PNG",
            data=buffer.getvalue(),
            file_name=f"{key}.png",
            mime="image/png",
        )
        plt.close(fig)

