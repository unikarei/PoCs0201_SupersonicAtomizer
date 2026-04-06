from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.breakup import CriticalWeberBreakupModel
from supersonic_atomizer.domain import BoundaryConditionConfig, DropletInjectionConfig, GeometryConfig
from supersonic_atomizer.geometry import build_geometry_model
from supersonic_atomizer.solvers.droplet import solve_droplet_transport
from supersonic_atomizer.solvers.gas import solve_quasi_1d_gas_flow
from supersonic_atomizer.thermo import AirThermoProvider


class TestRuntimeBreakupIntegration(unittest.TestCase):
    def test_applies_breakup_diameter_updates_in_transport_flow(self) -> None:
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
            breakup_model=CriticalWeberBreakupModel(
                critical_weber_number=1.0,
                breakup_factor_mean=0.5,
                breakup_factor_max=0.75,
            ),
        )

        self.assertFalse(droplet_solution.breakup_flags[0])
        self.assertTrue(any(droplet_solution.breakup_flags[1:]))

        first_trigger_index = droplet_solution.breakup_flags.index(True)
        self.assertLess(
            droplet_solution.mean_diameter_values[first_trigger_index],
            droplet_solution.mean_diameter_values[first_trigger_index - 1],
        )
        self.assertLess(
            droplet_solution.maximum_diameter_values[first_trigger_index],
            droplet_solution.maximum_diameter_values[first_trigger_index - 1],
        )
        self.assertEqual(droplet_solution.diagnostics.status, "completed")


if __name__ == "__main__":
    unittest.main()