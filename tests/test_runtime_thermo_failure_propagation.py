from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.common import ModelSelectionError, ThermoError
from supersonic_atomizer.domain import (
    BoundaryConditionConfig,
    CaseConfig,
    DropletInjectionConfig,
    FluidConfig,
    GeometryConfig,
    ModelSelectionConfig,
    OutputConfig,
)
from supersonic_atomizer.thermo import AirThermoProvider, evaluate_thermo_state, select_thermo_provider


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


class TestRuntimeThermoFailurePropagation(unittest.TestCase):
    def test_invalid_state_requests_surface_as_thermo_errors(self) -> None:
        provider = AirThermoProvider()

        with self.assertRaises(ThermoError):
            evaluate_thermo_state(provider, pressure=0.0, temperature=300.0)

        with self.assertRaises(ThermoError):
            evaluate_thermo_state(provider, pressure=101325.0, temperature=-5.0)

    def test_out_of_range_requests_surface_as_thermo_errors(self) -> None:
        provider = AirThermoProvider()

        with self.assertRaises(ThermoError):
            evaluate_thermo_state(provider, pressure=50.0, temperature=300.0)

        with self.assertRaises(ThermoError):
            evaluate_thermo_state(provider, pressure=101325.0, temperature=2500.0)

    def test_unsupported_backend_selection_remains_model_selection_error(self) -> None:
        case_config = _build_case_config(
            working_fluid="steam",
            steam_property_model="if97_stub",
        )

        with self.assertRaises(ModelSelectionError):
            select_thermo_provider(case_config)


if __name__ == "__main__":
    unittest.main()