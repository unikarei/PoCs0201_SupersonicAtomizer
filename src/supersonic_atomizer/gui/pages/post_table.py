"""Post Tab 2 — results table and CSV export (P23-T09, updated P24-T05)."""

from __future__ import annotations

import csv
import io

from supersonic_atomizer.domain import SimulationResult
from supersonic_atomizer.gui.unit_settings import FIELD_UNIT_GROUP, convert_value, display_unit_label


def result_to_table_rows(
    simulation_result: SimulationResult,
    unit_preferences: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    """Convert SimulationResult to row dicts suitable for a table view.

    Parameters
    ----------
    simulation_result:
        The completed simulation result.
    unit_preferences:
        Optional mapping of unit-group name → display unit label (from
        ``GUIState.unit_preferences()``).  When ``None`` all values are
        returned in SI units with bare column names — backward-compatible
        with existing tests.  When provided, dimensioned values are
        converted and column headers get a ``" [unit]"`` suffix.
    """

    def _col(field: str) -> str:
        """Return the column key: bare when no prefs, 'field [unit]' when prefs provided."""
        if unit_preferences is None:
            return field
        group = FIELD_UNIT_GROUP.get(field)
        if group is None:
            return field  # dimensionless or boolean — no suffix
        unit = display_unit_label(group, unit_preferences)
        return f"{field} [{unit}]"

    def _val(si_value: object, field: str) -> object:
        """Convert a dimensioned SI value; leave booleans and dimensionless unchanged."""
        if unit_preferences is None:
            return si_value
        if not isinstance(si_value, (int, float)) or isinstance(si_value, bool):
            return si_value
        group = FIELD_UNIT_GROUP.get(field)
        if group is None:
            return si_value
        return convert_value(float(si_value), group, unit_preferences)

    rows: list[dict[str, object]] = []
    for index, x_value in enumerate(simulation_result.gas_solution.x_values):
        rows.append(
            {
                _col("x"):                        _val(x_value, "x"),
                _col("A"):                        _val(simulation_result.gas_solution.area_values[index], "A"),
                _col("pressure"):                 _val(simulation_result.gas_solution.pressure_values[index], "pressure"),
                _col("temperature"):              _val(simulation_result.gas_solution.temperature_values[index], "temperature"),
                _col("density"):                  _val(simulation_result.gas_solution.density_values[index], "density"),
                _col("working_fluid_velocity"):   _val(simulation_result.gas_solution.velocity_values[index], "working_fluid_velocity"),
                _col("Mach_number"):              simulation_result.gas_solution.mach_number_values[index],
                _col("droplet_velocity"):         _val(simulation_result.droplet_solution.velocity_values[index], "droplet_velocity"),
                _col("slip_velocity"):            _val(simulation_result.droplet_solution.slip_velocity_values[index], "slip_velocity"),
                _col("droplet_mean_diameter"):    _val(simulation_result.droplet_solution.mean_diameter_values[index], "droplet_mean_diameter"),
                _col("droplet_maximum_diameter"): _val(simulation_result.droplet_solution.maximum_diameter_values[index], "droplet_maximum_diameter"),
                _col("Weber_number"):             simulation_result.droplet_solution.weber_number_values[index],
                "breakup_flag":                   simulation_result.droplet_solution.breakup_flags[index],
                _col("droplet_reynolds_number"):  simulation_result.droplet_solution.reynolds_number_values[index],
            }
        )
    return rows


def generate_csv_content(rows: list[dict[str, object]]) -> str:
    """Generate CSV text from table rows.

    Column headers are taken directly from the row dict keys, so they
    automatically include any unit suffix added by ``result_to_table_rows``
    when unit_preferences are provided.
    """
    if not rows:
        return ""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def render_post_table() -> None:
    """Render the Post Tab 2 results table with user-selected display units."""
    import pandas as pd
    import streamlit as st

    state = st.session_state.gui_state
    if state.last_run_result is None or state.last_run_result.simulation_result is None:
        st.info("Run a simulation to display the results table.")
        return

    prefs = state.unit_preferences()
    rows = result_to_table_rows(state.last_run_result.simulation_result, prefs)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.download_button(
        label="Export table as CSV",
        data=generate_csv_content(rows),
        file_name="results_table.csv",
        mime="text/csv",
    )

