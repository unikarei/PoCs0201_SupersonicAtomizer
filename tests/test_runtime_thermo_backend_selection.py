from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.common import ModelSelectionError
from supersonic_atomizer.domain import (
    BoundaryConditionConfig,
    CaseConfig,
    DropletInjectionConfig,
    FluidConfig,
    GeometryConfig,
    ModelSelectionConfig,
    OutputConfig,
)
from supersonic_atomizer.thermo import AirThermoProvider, SteamThermoProvider, select_thermo_provider


def _build_case_config(*, working_fluid: str, steam_property_model: str | None = None) -> CaseConfig:
    return CaseConfig(
        fluid=FluidConfig(working_fluid=working_fluid),
        boundary_conditions=BoundaryConditionConfig(
            Pt_in=500000.0,
            Tt_in=450.0,
            Ps_out=100000.0,
        ),
        geometry=GeometryConfig(
            x_start=0.0,
            x_end=0.1,
            n_cells=10,
            area_definition={
                "type": "table",
                "x": [0.0, 0.1],
                "A": [1.0e-4, 1.2e-4],
            },
        ),
        droplet_injection=DropletInjectionConfig(
            droplet_velocity_in=10.0,
            droplet_diameter_mean_in=1.0e-4,
            droplet_diameter_max_in=2.0e-4,
        ),
        models=ModelSelectionConfig(steam_property_model=steam_property_model),
        outputs=OutputConfig(),
    )


class TestRuntimeThermoBackendSelection(unittest.TestCase):
    def test_selects_air_provider_for_supported_air_case(self) -> None:
        case_config = _build_case_config(working_fluid="air", steam_property_model="ignored_backend")

        provider = select_thermo_provider(case_config)

        self.assertIsInstance(provider, AirThermoProvider)
        self.assertEqual(provider.working_fluid, "air")

    def test_selects_default_steam_provider_without_explicit_backend(self) -> None:
        case_config = _build_case_config(working_fluid="steam")

        provider = select_thermo_provider(case_config)

        self.assertIsInstance(provider, SteamThermoProvider)
        self.assertEqual(provider.working_fluid, "steam")

    def test_selects_supported_named_steam_backend(self) -> None:
        case_config = _build_case_config(
            working_fluid="steam",
            steam_property_model="equilibrium_mvp",
        )

        provider = select_thermo_provider(case_config)

        self.assertIsInstance(provider, SteamThermoProvider)

    def test_rejects_unsupported_steam_backend_name(self) -> None:
        case_config = _build_case_config(
            working_fluid="steam",
            steam_property_model="unsupported_backend",
        )

        with self.assertRaises(ModelSelectionError):
            select_thermo_provider(case_config)

    def test_rejects_unsupported_working_fluid_name(self) -> None:
        case_config = _build_case_config(working_fluid="argon")

        with self.assertRaises(ModelSelectionError):
            select_thermo_provider(case_config)


if __name__ == "__main__":
    unittest.main()