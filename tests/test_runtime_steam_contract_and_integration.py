from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.app import create_application_service
from supersonic_atomizer.domain import BoundaryConditionConfig, GeometryConfig
from supersonic_atomizer.geometry import build_geometry_model
from supersonic_atomizer.solvers.gas import solve_quasi_1d_gas_flow
from supersonic_atomizer.thermo import SteamThermoProvider


class TestRuntimeSteamContractAndIntegration(unittest.TestCase):
    def test_steam_provider_is_deterministic_for_equivalent_queries(self) -> None:
        provider = SteamThermoProvider()

        first_state = provider.evaluate_state(pressure=200000.0, temperature=450.0)
        second_state = provider.evaluate_state(pressure=200000.0, temperature=450.0)

        self.assertEqual(first_state, second_state)
        self.assertEqual(provider.metadata.provider_name, "equilibrium_steam_mvp")

    def test_steam_provider_supports_gas_only_execution_case(self) -> None:
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
            boundary_conditions=BoundaryConditionConfig(
                Pt_in=205000.0,
                Tt_in=450.0,
                Ps_out=200000.0,
            ),
            thermo_provider=SteamThermoProvider(),
        )

        self.assertEqual(gas_solution.diagnostics.status, "completed")
        self.assertTrue(all(value > 0.0 for value in gas_solution.temperature_values))
        self.assertTrue(all(value > 0.0 for value in gas_solution.density_values))

    def test_steam_startup_flow_resolves_runtime_provider(self) -> None:
        service = create_application_service()
        case_yaml = """
fluid:
  working_fluid: steam
boundary_conditions:
  Pt_in: 205000.0
  Tt_in: 450.0
  Ps_out: 200000.0
geometry:
  x_start: 0.0
  x_end: 0.1
  n_cells: 4
  area_distribution:
    type: table
    x: [0.0, 0.1]
    A: [0.0001, 0.0001]
droplet_injection:
  droplet_velocity_in: 5.0
  droplet_diameter_mean_in: 0.0001
  droplet_diameter_max_in: 0.0002
models:
  steam_property_model: equilibrium_mvp
  breakup_factor_mean: 0.5
  breakup_factor_max: 0.75
""".strip()

        with tempfile.TemporaryDirectory() as temporary_directory:
            case_path = Path(temporary_directory) / "steam_case.yaml"
            case_path.write_text(case_yaml, encoding="utf-8")

            startup_result = service.run_startup(str(case_path))

        self.assertEqual(startup_result.status, "ready")
        self.assertEqual(
            startup_result.startup_dependencies.thermo_provider.working_fluid,
            "steam",
        )


if __name__ == "__main__":
    unittest.main()