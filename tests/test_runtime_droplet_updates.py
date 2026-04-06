from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.domain import DropletInjectionConfig, GasState, ThermoState
from supersonic_atomizer.solvers.droplet import (
    StandardSphereDragModel,
    initialize_droplet_state,
    update_droplet_state,
)


def _build_gas_state(*, x: float, velocity: float, density: float = 1.2) -> GasState:
    thermo_state = ThermoState(
        pressure=100000.0,
        temperature=300.0,
        density=density,
        enthalpy=300000.0,
        sound_speed=340.0,
    )
    return GasState(
        x=x,
        area=1.0e-4,
        pressure=100000.0,
        temperature=300.0,
        density=density,
        velocity=velocity,
        mach_number=velocity / thermo_state.sound_speed,
        thermo_state=thermo_state,
    )


class TestRuntimeDropletUpdates(unittest.TestCase):
    def test_initialization_preserves_zero_slip_case(self) -> None:
        gas_state = _build_gas_state(x=0.0, velocity=10.0)
        droplet_state = initialize_droplet_state(
            gas_state=gas_state,
            injection_config=DropletInjectionConfig(
                droplet_velocity_in=10.0,
                droplet_diameter_mean_in=1.0e-4,
                droplet_diameter_max_in=2.0e-4,
            ),
            drag_model=StandardSphereDragModel(),
        )

        self.assertEqual(droplet_state.velocity, 10.0)
        self.assertEqual(droplet_state.slip_velocity, 0.0)
        self.assertEqual(droplet_state.weber_number, 0.0)
        self.assertEqual(droplet_state.reynolds_number, 0.0)

    def test_local_update_increases_velocity_for_positive_slip(self) -> None:
        initial_state = initialize_droplet_state(
            gas_state=_build_gas_state(x=0.0, velocity=20.0),
            injection_config=DropletInjectionConfig(
                droplet_velocity_in=5.0,
                droplet_diameter_mean_in=1.0e-4,
                droplet_diameter_max_in=2.0e-4,
            ),
            drag_model=StandardSphereDragModel(),
        )

        updated_state = update_droplet_state(
            previous_state=initial_state,
            gas_state=_build_gas_state(x=0.02, velocity=20.0),
            dx_value=0.02,
            drag_model=StandardSphereDragModel(),
        )

        self.assertGreater(updated_state.velocity, initial_state.velocity)
        self.assertLess(abs(updated_state.slip_velocity), abs(initial_state.slip_velocity))
        self.assertGreaterEqual(updated_state.weber_number, 0.0)


if __name__ == "__main__":
    unittest.main()