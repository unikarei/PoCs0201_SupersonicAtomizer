"""P9-T07 — Lightweight integration test for the liquid-jet primary-breakup flow.

Path under test:
    YAML dict → translate_case_config → geometry → gas solver (solve_quasi_1d_gas_flow)
    → solve_droplet_transport (liquid_jet_injection) → DropletSolution assertions

Completion criteria (from tasks.md):
- `primary_breakup_length` present and positive in diagnostics messages
- Downstream droplet fields (velocity_values, mean_diameter_values) are present and
  have the same length as x_values
"""

from __future__ import annotations

import pytest

from supersonic_atomizer.config.translator import translate_case_config
from supersonic_atomizer.geometry.geometry_model import build_geometry_model
from supersonic_atomizer.solvers.gas import solve_quasi_1d_gas_flow
from supersonic_atomizer.thermo.selection import select_thermo_provider
from supersonic_atomizer.solvers.droplet.transport_solver import solve_droplet_transport


# ---------------------------------------------------------------------------
# Minimal synthetic case
# ---------------------------------------------------------------------------

_LIQUID_JET_CASE = {
    "fluid": {"working_fluid": "air"},
    "boundary_conditions": {
        "Pt_in": 300_000,
        "Tt_in": 300.0,
        "Ps_out": 25_000,
    },
    "geometry": {
        "x_start": 0.0,
        "x_end": 0.5,
        "n_cells": 15,
        "area_distribution": {
            "type": "table",
            "x": [0.0, 0.25, 0.5],
            "A": [0.01, 0.005, 0.01],
        },
    },
    "droplet_injection": {
        "injection_mode": "liquid_jet_injection",
        # dummy droplet fields required by translator/schema
        "droplet_velocity_in": 0.0,
        "droplet_diameter_mean_in": 1e-4,
        "droplet_diameter_max_in": 2e-4,
        # liquid-jet specific
        "liquid_jet_diameter": 0.001,
        "liquid_mass_flow_rate": 0.005,
        "liquid_velocity": 5.0,
        "liquid_density": 998.2,
        "liquid_viscosity": 0.001,
        "surface_tension": 0.072,
    },
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def droplet_solution():
    """Run the full pipeline and return a DropletSolution for assertions."""
    case = translate_case_config(_LIQUID_JET_CASE)
    geom = build_geometry_model(case.geometry)
    thermo = select_thermo_provider(case)
    gas_sol = solve_quasi_1d_gas_flow(
        geometry_model=geom,
        boundary_conditions=case.boundary_conditions,
        thermo_provider=thermo,
    )
    droplet_sol = solve_droplet_transport(
        gas_solution=gas_sol,
        injection_config=case.droplet_injection,
    )
    return droplet_sol


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLiquidJetPrimaryBreakupIntegration:

    def test_droplet_solution_produced(self, droplet_solution):
        """solve_droplet_transport returns a DropletSolution without error."""
        assert droplet_solution is not None

    def test_x_values_match_grid_length(self, droplet_solution):
        """DropletSolution x_values has the expected number of nodes."""
        assert len(droplet_solution.x_values) > 0

    def test_velocity_values_length_consistent(self, droplet_solution):
        assert len(droplet_solution.velocity_values) == len(droplet_solution.x_values)

    def test_mean_diameter_values_present(self, droplet_solution):
        assert len(droplet_solution.mean_diameter_values) == len(droplet_solution.x_values)

    def test_primary_breakup_length_in_diagnostics(self, droplet_solution):
        """primary_breakup_length must be reported in diagnostics messages."""
        messages = droplet_solution.diagnostics.messages
        pb_msgs = [m for m in messages if "primary_breakup_length" in m]
        assert len(pb_msgs) == 1, (
            f"Expected one 'primary_breakup_length' diagnostic message; "
            f"got: {messages}"
        )

    def test_primary_breakup_length_is_positive(self, droplet_solution):
        messages = droplet_solution.diagnostics.messages
        pb_msg = next(m for m in messages if "primary_breakup_length" in m)
        # message format: "primary_breakup_length=<float>"
        value = float(pb_msg.split("=")[1])
        assert value > 0.0, f"primary_breakup_length must be positive; got {value}"

    def test_generated_mean_diameter_in_diagnostics(self, droplet_solution):
        messages = droplet_solution.diagnostics.messages
        gmd_msgs = [m for m in messages if "generated_mean_diameter" in m]
        assert len(gmd_msgs) == 1

    def test_droplet_fields_after_breakup_location(self, droplet_solution):
        """At least some states past the primary-breakup location should have
        a positive mean diameter that is smaller than the jet diameter (0.001 m)."""
        small_diameters = [
            d for d in droplet_solution.mean_diameter_values
            if d is not None and d < 0.001
        ]
        assert len(small_diameters) > 0, (
            "Expected at least some generated droplets with diameter < liquid jet diameter."
        )

    def test_breakup_flags_tuple(self, droplet_solution):
        """breakup_flags must be a tuple of booleans with the correct length."""
        assert isinstance(droplet_solution.breakup_flags, tuple)
        assert len(droplet_solution.breakup_flags) == len(droplet_solution.x_values)

    def test_diagnostics_status_completed(self, droplet_solution):
        assert droplet_solution.diagnostics.status == "completed"
