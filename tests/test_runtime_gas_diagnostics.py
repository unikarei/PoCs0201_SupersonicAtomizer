from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.common import NumericalError
from supersonic_atomizer.domain import BoundaryConditionConfig, GeometryConfig
from supersonic_atomizer.geometry import build_geometry_model
from supersonic_atomizer.solvers.gas import solve_quasi_1d_gas_flow
from supersonic_atomizer.thermo import AirThermoProvider


class TestRuntimeGasDiagnostics(unittest.TestCase):
    def test_solver_surfaces_incomplete_progression_for_branch_ambiguity_case(self) -> None:
        geometry_model = build_geometry_model(
            GeometryConfig(
                x_start=0.0,
                x_end=0.1,
                n_cells=2,
                area_definition={
                    "type": "table",
                    "x": [0.0, 0.05, 0.1],
                    "A": [1.4e-4, 0.8e-4, 1.4e-4],
                },
            )
        )

        with self.assertRaises(NumericalError) as context:
            solve_quasi_1d_gas_flow(
                geometry_model=geometry_model,
                boundary_conditions=BoundaryConditionConfig(
                    Pt_in=150000.0,
                    Tt_in=320.0,
                    Ps_out=100000.0,
                ),
                thermo_provider=AirThermoProvider(),
            )

        self.assertIn("Branch ambiguity diagnostics", str(context.exception))
        self.assertIn("location=x=0.050000", str(context.exception))
        self.assertIn("last_valid_state=", str(context.exception))

    def test_solver_rejects_nonphysical_local_update_states(self) -> None:
        geometry_model = build_geometry_model(
            GeometryConfig(
                x_start=0.0,
                x_end=0.1,
                n_cells=1,
                area_definition={
                    "type": "table",
                    "x": [0.0, 0.1],
                    "A": [1.0e-4, 1.0e-4],
                },
            )
        )

        with self.assertRaises(NumericalError):
            solve_quasi_1d_gas_flow(
                geometry_model=geometry_model,
                boundary_conditions=BoundaryConditionConfig(
                    Pt_in=500000.0,
                    Tt_in=320.0,
                    Ps_out=100000.0,
                ),
                thermo_provider=AirThermoProvider(),
            )


if __name__ == "__main__":
    unittest.main()