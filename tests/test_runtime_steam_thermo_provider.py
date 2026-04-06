from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.common import ThermoError
from supersonic_atomizer.domain import ThermoState
from supersonic_atomizer.thermo import SteamThermoProvider, ThermoProvider


class TestRuntimeSteamThermoProvider(unittest.TestCase):
    def test_steam_provider_implements_runtime_thermo_interface(self) -> None:
        provider = SteamThermoProvider()

        self.assertIsInstance(provider, ThermoProvider)
        self.assertEqual(provider.provider_name, "equilibrium_steam_mvp")
        self.assertEqual(provider.working_fluid, "steam")
        self.assertTrue(provider.validity_notes)

    def test_steam_provider_evaluates_representative_si_state(self) -> None:
        provider = SteamThermoProvider()

        state = provider.evaluate_state(pressure=200000.0, temperature=450.0)

        self.assertIsInstance(state, ThermoState)
        self.assertEqual(state.pressure, 200000.0)
        self.assertEqual(state.temperature, 450.0)
        self.assertGreater(state.density, 0.0)
        self.assertGreater(state.enthalpy, 0.0)
        self.assertGreater(state.sound_speed, 0.0)

    def test_steam_provider_rejects_invalid_or_out_of_range_states(self) -> None:
        provider = SteamThermoProvider()

        with self.assertRaises(ThermoError):
            provider.evaluate_state(pressure=0.0, temperature=450.0)
        with self.assertRaises(ThermoError):
            provider.evaluate_state(pressure=200000.0, temperature=250.0)


if __name__ == "__main__":
    unittest.main()