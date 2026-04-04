from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.domain import ThermoState
from supersonic_atomizer.thermo import ThermoProvider, ThermoProviderMetadata


class _StubThermoProvider(ThermoProvider):
    @property
    def metadata(self) -> ThermoProviderMetadata:
        return ThermoProviderMetadata(
            provider_name="stub_provider",
            working_fluid="air",
            validity_notes=("test-only provider",),
        )

    def evaluate_state(self, *, pressure: float, temperature: float) -> ThermoState:
        return ThermoState(
            pressure=pressure,
            temperature=temperature,
            density=1.0,
            enthalpy=1000.0,
            sound_speed=300.0,
        )


class TestRuntimeThermoProviderInterface(unittest.TestCase):
    def test_interface_requires_metadata_and_state_evaluation(self) -> None:
        with self.assertRaises(TypeError):
            ThermoProvider()

    def test_runtime_provider_metadata_shape_is_available(self) -> None:
        provider = _StubThermoProvider()

        self.assertEqual(provider.provider_name, "stub_provider")
        self.assertEqual(provider.working_fluid, "air")
        self.assertEqual(provider.validity_notes, ("test-only provider",))
        self.assertEqual(provider.metadata.provider_name, "stub_provider")

    def test_state_evaluation_returns_runtime_thermo_state(self) -> None:
        provider = _StubThermoProvider()

        state = provider.evaluate_state(pressure=101325.0, temperature=300.0)

        self.assertIsInstance(state, ThermoState)
        self.assertEqual(state.pressure, 101325.0)
        self.assertEqual(state.temperature, 300.0)
        self.assertEqual(state.density, 1.0)
        self.assertEqual(state.enthalpy, 1000.0)
        self.assertEqual(state.sound_speed, 300.0)


if __name__ == "__main__":
    unittest.main()