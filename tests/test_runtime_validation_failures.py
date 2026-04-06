from dataclasses import replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.app.result_assembly import assemble_simulation_result
from supersonic_atomizer.common import ValidationError
from supersonic_atomizer.domain import BoundaryConditionConfig, CaseConfig, DropletInjectionConfig, FluidConfig, GeometryConfig, ModelSelectionConfig, OutputConfig
from supersonic_atomizer.geometry import build_geometry_model
from supersonic_atomizer.solvers.droplet import solve_droplet_transport
from supersonic_atomizer.solvers.gas import solve_quasi_1d_gas_flow
from supersonic_atomizer.thermo import AirThermoProvider
from supersonic_atomizer.validation import run_sanity_checks


def _build_result():
    case_config = CaseConfig(
        fluid=FluidConfig(working_fluid="air"),
        boundary_conditions=BoundaryConditionConfig(Pt_in=105000.0, Tt_in=300.0, Ps_out=100000.0),
        geometry=GeometryConfig(
            x_start=0.0,
            x_end=0.1,
            n_cells=4,
            area_definition={"type": "table", "x": [0.0, 0.1], "A": [1.0e-4, 1.0e-4]},
        ),
        droplet_injection=DropletInjectionConfig(
            droplet_velocity_in=1.0,
            droplet_diameter_mean_in=1.0e-4,
            droplet_diameter_max_in=2.0e-4,
        ),
        models=ModelSelectionConfig(breakup_factor_mean=0.5, breakup_factor_max=0.75),
        outputs=OutputConfig(output_directory="outputs"),
    )
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
    return assemble_simulation_result(
        case_config=case_config,
        gas_solution=gas_solution,
        droplet_solution=droplet_solution,
    )


class TestRuntimeValidationFailures(unittest.TestCase):
    def test_rejects_misaligned_result_inputs(self) -> None:
        simulation_result = _build_result()
        bad_droplet_solution = replace(
            simulation_result.droplet_solution,
            x_values=tuple(value + 1.0e-3 for value in simulation_result.droplet_solution.x_values),
        )
        bad_result = replace(simulation_result, droplet_solution=bad_droplet_solution)

        with self.assertRaises(ValidationError):
            run_sanity_checks(bad_result)


if __name__ == "__main__":
    unittest.main()