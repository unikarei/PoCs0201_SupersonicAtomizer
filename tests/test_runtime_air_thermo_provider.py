from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.common import ThermoError
from supersonic_atomizer.domain import ThermoState
from supersonic_atomizer.thermo import AirThermoProvider, ThermoProvider


class TestRuntimeAirThermoProvider(unittest.TestCase):
    def test_air_provider_implements_runtime_thermo_interface(self) -> None:
        provider = AirThermoProvider()

        self.assertIsInstance(provider, ThermoProvider)
        self.assertEqual(provider.provider_name, "ideal_air")
        self.assertEqual(provider.working_fluid, "air")
        self.assertTrue(provider.validity_notes)

    def test_air_provider_evaluates_representative_si_state(self) -> None:
        provider = AirThermoProvider()

        state = provider.evaluate_state(pressure=101325.0, temperature=300.0)

        self.assertIsInstance(state, ThermoState)
        self.assertEqual(state.pressure, 101325.0)
        self.assertEqual(state.temperature, 300.0)
        self.assertAlmostEqual(state.density, 1.176624281484062, places=12)
        self.assertAlmostEqual(state.enthalpy, 301402.5, places=7)
        self.assertAlmostEqual(state.sound_speed, 347.2189510957027, places=12)

    def test_air_provider_rejects_nonphysical_pressure_and_temperature(self) -> None:
        provider = AirThermoProvider()

        with self.assertRaises(ThermoError):
            provider.evaluate_state(pressure=0.0, temperature=300.0)

        with self.assertRaises(ThermoError):
            provider.evaluate_state(pressure=101325.0, temperature=-1.0)


if __name__ == "__main__":
    unittest.main()