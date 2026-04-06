from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.domain import BoundaryConditionConfig, DropletInjectionConfig, DropletSolution, GeometryConfig
from supersonic_atomizer.geometry import build_geometry_model
from supersonic_atomizer.solvers.droplet import solve_droplet_transport
from supersonic_atomizer.solvers.gas import solve_quasi_1d_gas_flow
from supersonic_atomizer.thermo import AirThermoProvider


class TestRuntimeDropletTransportSolver(unittest.TestCase):
    def test_solves_zero_slip_transport_case(self) -> None:
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
            boundary_conditions=BoundaryConditionConfig(Pt_in=105000.0, Tt_in=300.0, Ps_out=100000.0),
            thermo_provider=AirThermoProvider(),
        )

        droplet_solution = solve_droplet_transport(
            gas_solution=gas_solution,
            injection_config=DropletInjectionConfig(
                droplet_velocity_in=gas_solution.velocity_values[0],
                droplet_diameter_mean_in=1.0e-4,
                droplet_diameter_max_in=2.0e-4,
            ),
        )

        self.assertIsInstance(droplet_solution, DropletSolution)
        self.assertEqual(len(droplet_solution.states), len(gas_solution.states))
        self.assertTrue(all(abs(value) < 1.0e-10 for value in droplet_solution.slip_velocity_values))
        self.assertTrue(all(flag is False for flag in droplet_solution.breakup_flags))

    def test_solves_slip_driven_transport_case_without_breakup(self) -> None:
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
            boundary_conditions=BoundaryConditionConfig(Pt_in=105000.0, Tt_in=300.0, Ps_out=100000.0),
            thermo_provider=AirThermoProvider(),
        )

        droplet_solution = solve_droplet_transport(
            gas_solution=gas_solution,
            injection_config=DropletInjectionConfig(
                droplet_velocity_in=1.0,
                droplet_diameter_mean_in=1.0e-4,
                droplet_diameter_max_in=2.0e-4,
            ),
        )

        self.assertGreater(droplet_solution.velocity_values[-1], droplet_solution.velocity_values[0])
        self.assertLess(abs(droplet_solution.slip_velocity_values[-1]), abs(droplet_solution.slip_velocity_values[0]))
        self.assertEqual(droplet_solution.diagnostics.status, "completed")


if __name__ == "__main__":
    unittest.main()