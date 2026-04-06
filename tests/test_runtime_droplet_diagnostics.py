from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.common import NumericalError
from supersonic_atomizer.domain import DropletInjectionConfig, DropletState, GasSolution
from supersonic_atomizer.solvers.droplet import StandardSphereDragModel, solve_droplet_transport
from supersonic_atomizer.solvers.droplet.diagnostics import validate_droplet_state


class TestRuntimeDropletDiagnostics(unittest.TestCase):
    def test_validate_droplet_state_rejects_invalid_metrics(self) -> None:
        with self.assertRaises(NumericalError):
            validate_droplet_state(
                DropletState(
                    x=0.0,
                    velocity=-1.0,
                    slip_velocity=0.0,
                    mean_diameter=1.0e-4,
                    maximum_diameter=2.0e-4,
                    weber_number=0.0,
                )
            )

    def test_transport_solver_rejects_empty_gas_solution(self) -> None:
        empty_gas_solution = GasSolution(
            states=(),
            x_values=(),
            area_values=(),
            pressure_values=(),
            temperature_values=(),
            density_values=(),
            velocity_values=(),
            mach_number_values=(),
        )

        with self.assertRaises(NumericalError):
            solve_droplet_transport(
                gas_solution=empty_gas_solution,
                injection_config=DropletInjectionConfig(
                    droplet_velocity_in=1.0,
                    droplet_diameter_mean_in=1.0e-4,
                    droplet_diameter_max_in=2.0e-4,
                ),
                drag_model=StandardSphereDragModel(),
            )


if __name__ == "__main__":
    unittest.main()