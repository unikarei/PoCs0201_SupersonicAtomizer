"""GUI-side session state model.

Stores all mutable GUI state in a plain Python dataclass.
In Streamlit, an instance of GUIState is stored under ``st.session_state``
so it survives UI reruns.

This module has no Streamlit dependency — it is a pure Python data model
that can be constructed and tested without a running Streamlit server.

Boundary: imports only from app/services.py (result types) and stdlib.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from supersonic_atomizer.app.services import SimulationRunResult
from supersonic_atomizer.gui.multi_run import MultiRunSimulationResult


@dataclass
class GUIState:
    """Mutable GUI session state.

    All fields have defaults so an instance can be created with no arguments,
    giving a sensible starting state for a new case.

    Units are SI throughout, consistent with the rest of the application.
    """

    # ── Case management ────────────────────────────────────────────────────────
    active_case_name: str | None = None
    active_case_path: str | None = None

    # ── Pre Tab 1 — Analysis conditions ───────────────────────────────────────
    working_fluid: str = "air"
    inlet_total_pressure: float = 200_000.0     # Pa
    inlet_total_temperature: float = 400.0       # K
    outlet_static_pressure: float = 101_325.0   # Pa
    inlet_wetness: float | None = None           # dimensionless; steam only

    # Droplet injection
    droplet_velocity_in: float = 10.0           # m/s
    droplet_diameter_mean_in: float = 50e-6     # m
    droplet_diameter_max_in: float = 100e-6     # m

    # Breakup model
    critical_weber_number: float = 12.0
    breakup_factor_mean: float = 0.5
    breakup_factor_max: float = 0.5

    # ── Pre Tab 2 — Grid definition ────────────────────────────────────────────
    x_start: float = 0.0     # m
    x_end: float = 0.1       # m
    n_cells: int = 100
    # Editable (x, A) table — list of dicts to remain pandas-free in state layer.
    # Streamlit's st.data_editor converts this to/from a DataFrame at the UI boundary.
    area_table: list[dict[str, Any]] = field(
        default_factory=lambda: [
            {"x": 0.0,   "A": 1.0e-4},
            {"x": 0.05,  "A": 6.0e-5},
            {"x": 0.10,  "A": 5.0e-5},
        ]
    )

    # ── Unit preferences (display only — solver values remain SI) ──────────────
    # One field per quantity group, matching UNIT_GROUPS keys in unit_settings.py.
    # These affect only Post tab plots and the results table export.
    unit_pressure:    str = "kPa"
    unit_temperature: str = "K"
    unit_velocity:    str = "m/s"
    unit_diameter:    str = "μm"
    unit_length:      str = "m"
    unit_area:        str = "m²"
    unit_density:     str = "kg/m³"

    # ── Solver execution state ─────────────────────────────────────────────────
    solver_running: bool = False
    last_run_result: SimulationRunResult | MultiRunSimulationResult | None = None
    solver_error: str | None = None

    # ── Transitions ────────────────────────────────────────────────────────────

    def mark_running(self) -> None:
        """Transition to running state immediately before solver invocation."""
        self.solver_running = True
        self.last_run_result = None
        self.solver_error = None

    def mark_complete(self, result: SimulationRunResult | MultiRunSimulationResult) -> None:
        """Transition to idle state after the solver returns a result."""
        self.solver_running = False
        self.last_run_result = result

    def mark_error(self, message: str) -> None:
        """Transition to idle state after an unexpected solver-invocation error."""
        self.solver_running = False
        self.solver_error = message

    def has_result(self) -> bool:
        """Return True when a completed run result is available for display."""
        return self.last_run_result is not None

    def result_is_success(self) -> bool:
        """Return True when the last run completed without a failure status."""
        return (
            self.last_run_result is not None
            and isinstance(self.last_run_result, SimulationRunResult)
            and self.last_run_result.status in {"completed", "output-failed"}
        )

    def unit_preferences(self) -> dict[str, str]:
        """Return a unit-preference dict compatible with gui.unit_settings helpers.

        The dict maps each quantity-group name to the user-selected display unit.
        All values in this dict are guaranteed to be valid keys in UNIT_GROUPS.
        """
        return {
            "pressure":    self.unit_pressure,
            "temperature": self.unit_temperature,
            "velocity":    self.unit_velocity,
            "diameter":    self.unit_diameter,
            "length":      self.unit_length,
            "area":        self.unit_area,
            "density":     self.unit_density,
        }
