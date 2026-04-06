from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.breakup import BreakupModelInputs, CriticalWeberBreakupModel
from supersonic_atomizer.common import ConfigurationError
from supersonic_atomizer.domain import DropletState, GasState, ThermoState


def _build_gas_state(*, velocity: float = 40.0, density: float = 1.2) -> GasState:
    thermo_state = ThermoState(
        pressure=100000.0,
        temperature=300.0,
        density=density,
        enthalpy=300000.0,
        sound_speed=340.0,
    )
    return GasState(
        x=0.02,
        area=1.0e-4,
        pressure=100000.0,
        temperature=300.0,
        density=density,
        velocity=velocity,
        mach_number=velocity / thermo_state.sound_speed,
        thermo_state=thermo_state,
    )


def _build_droplet_state(*, velocity: float, slip_velocity: float, weber_number: float = 0.0) -> DropletState:
    return DropletState(
        x=0.02,
        velocity=velocity,
        slip_velocity=slip_velocity,
        mean_diameter=1.0e-4,
        maximum_diameter=2.0e-4,
        weber_number=weber_number,
        reynolds_number=10.0,
        breakup_triggered=False,
    )


class TestRuntimeWeberCriticalBreakupModel(unittest.TestCase):
    def test_preserves_diameters_when_threshold_is_not_exceeded(self) -> None:
        breakup_model = CriticalWeberBreakupModel(
            critical_weber_number=20.0,
            breakup_factor_mean=0.5,
            breakup_factor_max=0.75,
        )

        decision = breakup_model.evaluate(
            BreakupModelInputs(
                gas_state=_build_gas_state(),
                droplet_state=_build_droplet_state(velocity=35.0, slip_velocity=5.0),
            )
        )

        self.assertFalse(decision.triggered)
        self.assertEqual(decision.updated_mean_diameter, 1.0e-4)
        self.assertEqual(decision.updated_maximum_diameter, 2.0e-4)

    def test_reduces_diameters_when_threshold_is_exceeded(self) -> None:
        breakup_model = CriticalWeberBreakupModel(
            critical_weber_number=1.0,
            breakup_factor_mean=0.5,
            breakup_factor_max=0.75,
        )

        decision = breakup_model.evaluate(
            BreakupModelInputs(
                gas_state=_build_gas_state(),
                droplet_state=_build_droplet_state(velocity=1.0, slip_velocity=39.0),
            )
        )

        self.assertTrue(decision.triggered)
        self.assertLess(decision.updated_mean_diameter, 1.0e-4)
        self.assertLess(decision.updated_maximum_diameter, 2.0e-4)
        self.assertGreaterEqual(decision.updated_maximum_diameter, decision.updated_mean_diameter)

    def test_rejects_invalid_breakup_parameters(self) -> None:
        with self.assertRaises(ConfigurationError):
            CriticalWeberBreakupModel(
                critical_weber_number=12.0,
                breakup_factor_mean=1.1,
                breakup_factor_max=0.75,
            )


if __name__ == "__main__":
    unittest.main()