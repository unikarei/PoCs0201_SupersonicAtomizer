from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.app import assemble_simulation_result
from supersonic_atomizer.domain import BoundaryConditionConfig, CaseConfig, DropletInjectionConfig, FluidConfig, GeometryConfig, ModelSelectionConfig, OutputConfig
from supersonic_atomizer.geometry import build_geometry_model
from supersonic_atomizer.solvers.droplet import solve_droplet_transport
from supersonic_atomizer.solvers.gas import solve_quasi_1d_gas_flow
from supersonic_atomizer.thermo import AirThermoProvider


def _make_case_config() -> CaseConfig:
    return CaseConfig(
        fluid=FluidConfig(working_fluid="air"),
        boundary_conditions=BoundaryConditionConfig(Pt_in=105000.0, Tt_in=300.0, Ps_out=100000.0),
        geometry=GeometryConfig(
            x_start=0.0,
            x_end=0.1,
            n_cells=4,
            area_definition={
                "type": "table",
                "x": [0.0, 0.1],
                "A": [1.0e-4, 1.0e-4],
            },
        ),
        droplet_injection=DropletInjectionConfig(
            droplet_velocity_in=1.0,
            droplet_diameter_mean_in=1.0e-4,
            droplet_diameter_max_in=2.0e-4,
        ),
        models=ModelSelectionConfig(
            breakup_factor_mean=0.5,
            breakup_factor_max=0.75,
        ),
        outputs=OutputConfig(output_directory="outputs"),
        case_name="air_phase19",
    )


class TestRuntimeResultAssembly(unittest.TestCase):
    def test_assembles_structured_simulation_result_with_aligned_fields(self) -> None:
        case_config = _make_case_config()
        geometry_model = build_geometry_model(case_config.geometry)
        gas_solution = solve_quasi_1d_gas_flow(
            geometry_model=geometry_model,
            boundary_conditions=case_config.boundary_conditions,
            thermo_provider=AirThermoProvider(),
        )
        droplet_solution = solve_droplet_transport(
            gas_solution=gas_solution,
            injection_config=case_config.droplet_injection,
        )

        simulation_result = assemble_simulation_result(
            case_config=case_config,
            gas_solution=gas_solution,
            droplet_solution=droplet_solution,
        )

        self.assertEqual(simulation_result.case_name, "air_phase19")
        self.assertEqual(simulation_result.working_fluid, "air")
        self.assertEqual(simulation_result.diagnostics.status, "completed")
        self.assertEqual(simulation_result.gas_solution.x_values, simulation_result.droplet_solution.x_values)
        self.assertEqual(simulation_result.settings_summary["models"]["drag_model"], "standard_sphere")


if __name__ == "__main__":
    unittest.main()