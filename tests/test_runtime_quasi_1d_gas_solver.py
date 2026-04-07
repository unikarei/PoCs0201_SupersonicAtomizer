from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.domain import BoundaryConditionConfig, GasSolution, GeometryConfig
from supersonic_atomizer.geometry import build_geometry_model
from supersonic_atomizer.solvers.gas import solve_quasi_1d_gas_flow
from supersonic_atomizer.thermo import AirThermoProvider


class TestRuntimeQuasi1DGasSolver(unittest.TestCase):
    def _build_laval_geometry(self):
        return build_geometry_model(
            GeometryConfig(
                x_start=0.0,
                x_end=0.2,
                n_cells=20,
                area_definition={
                    "type": "table",
                    "x": [0.0, 0.05, 0.1, 0.15, 0.2],
                    "A": [1.8e-4, 1.3e-4, 1.0e-4, 1.2e-4, 1.4e-4],
                },
            )
        )

    def test_solves_constant_area_gas_only_case(self) -> None:
        geometry_model = build_geometry_model(
            GeometryConfig(
                x_start=0.0,
                x_end=0.1,
                n_cells=4,
                area_definition={
                    "type": "table",
                    "x": [0.0, 0.1],
                    "A": [1.0e-4, 1.0e-4],
                },
            )
        )

        gas_solution = solve_quasi_1d_gas_flow(
            geometry_model=geometry_model,
            boundary_conditions=BoundaryConditionConfig(
                Pt_in=105000.0,
                Tt_in=300.0,
                Ps_out=100000.0,
            ),
            thermo_provider=AirThermoProvider(),
        )

        self.assertIsInstance(gas_solution, GasSolution)
        self.assertEqual(len(gas_solution.states), 5)
        self.assertEqual(gas_solution.x_values[0], 0.0)
        self.assertEqual(gas_solution.x_values[-1], 0.1)
        self.assertTrue(all(value > 0.0 for value in gas_solution.pressure_values))
        self.assertTrue(all(value > 0.0 for value in gas_solution.temperature_values))
        self.assertAlmostEqual(
            max(gas_solution.mach_number_values),
            min(gas_solution.mach_number_values),
            places=8,
        )
        self.assertEqual(gas_solution.diagnostics.status, "completed")

    def test_solves_converging_diverging_geometry_case_with_qualitative_mach_trend(self) -> None:
        geometry_model = build_geometry_model(
            GeometryConfig(
                x_start=0.0,
                x_end=0.2,
                n_cells=4,
                area_definition={
                    "type": "table",
                    "x": [0.0, 0.05, 0.1, 0.15, 0.2],
                    "A": [1.4e-4, 1.2e-4, 1.1e-4, 1.25e-4, 1.4e-4],
                },
            )
        )

        gas_solution = solve_quasi_1d_gas_flow(
            geometry_model=geometry_model,
            boundary_conditions=BoundaryConditionConfig(
                Pt_in=105000.0,
                Tt_in=320.0,
                Ps_out=100000.0,
            ),
            thermo_provider=AirThermoProvider(),
        )

        throat_index = gas_solution.area_values.index(min(gas_solution.area_values))
        throat_mach_number = gas_solution.mach_number_values[throat_index]

        self.assertGreater(throat_mach_number, gas_solution.mach_number_values[0])
        self.assertGreater(throat_mach_number, gas_solution.mach_number_values[-1])
        self.assertEqual(gas_solution.x_values[throat_index], 0.1)

    def test_solves_fully_supersonic_internal_laval_case(self) -> None:
        geometry_model = self._build_laval_geometry()

        gas_solution = solve_quasi_1d_gas_flow(
            geometry_model=geometry_model,
            boundary_conditions=BoundaryConditionConfig(
                Pt_in=300000.0,
                Tt_in=320.0,
                Ps_out=30000.0,
            ),
            thermo_provider=AirThermoProvider(),
        )

        throat_index = gas_solution.area_values.index(min(gas_solution.area_values))
        self.assertAlmostEqual(gas_solution.mach_number_values[throat_index], 1.0, places=6)
        self.assertGreater(gas_solution.mach_number_values[-1], 1.0)
        self.assertTrue(any("selected_branch=fully_supersonic_internal" in message for message in gas_solution.diagnostics.messages))

    def test_solves_internal_normal_shock_laval_case(self) -> None:
        geometry_model = self._build_laval_geometry()

        gas_solution = solve_quasi_1d_gas_flow(
            geometry_model=geometry_model,
            boundary_conditions=BoundaryConditionConfig(
                Pt_in=300000.0,
                Tt_in=320.0,
                Ps_out=200000.0,
            ),
            thermo_provider=AirThermoProvider(),
        )

        throat_index = gas_solution.area_values.index(min(gas_solution.area_values))
        diverging_mach = gas_solution.mach_number_values[throat_index + 1 :]

        self.assertTrue(any(value > 1.0 for value in diverging_mach))
        self.assertLess(gas_solution.mach_number_values[-1], 1.0)
        self.assertTrue(any("selected_branch=internal_normal_shock" in message or "selected_branch=exit_normal_shock" in message for message in gas_solution.diagnostics.messages))


if __name__ == "__main__":
    unittest.main()