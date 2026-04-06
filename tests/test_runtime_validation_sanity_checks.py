from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.app.result_assembly import assemble_simulation_result
from supersonic_atomizer.breakup import CriticalWeberBreakupModel
from supersonic_atomizer.domain import BoundaryConditionConfig, CaseConfig, DropletInjectionConfig, FluidConfig, GeometryConfig, ModelSelectionConfig, OutputConfig
from supersonic_atomizer.geometry import build_geometry_model
from supersonic_atomizer.solvers.droplet import solve_droplet_transport
from supersonic_atomizer.solvers.gas import solve_quasi_1d_gas_flow
from supersonic_atomizer.thermo import AirThermoProvider
from supersonic_atomizer.validation import run_sanity_checks, validate_simulation_result


def _build_case_config(*, droplet_velocity_in: float) -> CaseConfig:
    return CaseConfig(
        fluid=FluidConfig(working_fluid="air"),
        boundary_conditions=BoundaryConditionConfig(Pt_in=105000.0, Tt_in=300.0, Ps_out=100000.0),
        geometry=GeometryConfig(
            x_start=0.0,
            x_end=0.1,
            n_cells=4,
            area_definition={"type": "table", "x": [0.0, 0.1], "A": [1.0e-4, 1.0e-4]},
        ),
        droplet_injection=DropletInjectionConfig(
            droplet_velocity_in=droplet_velocity_in,
            droplet_diameter_mean_in=1.0e-4,
            droplet_diameter_max_in=2.0e-4,
        ),
        models=ModelSelectionConfig(breakup_factor_mean=0.5, breakup_factor_max=0.75),
        outputs=OutputConfig(output_directory="outputs"),
    )


def _build_result(*, zero_slip: bool, with_breakup: bool):
    case_config = _build_case_config(droplet_velocity_in=0.0 if not zero_slip else 0.0)
    geometry_model = build_geometry_model(case_config.geometry)
    gas_solution = solve_quasi_1d_gas_flow(
        geometry_model=geometry_model,
        boundary_conditions=case_config.boundary_conditions,
        thermo_provider=AirThermoProvider(),
    )
    injection_velocity = gas_solution.velocity_values[0] if zero_slip else 1.0
    case_config = _build_case_config(droplet_velocity_in=injection_velocity)
    breakup_model = None
    if with_breakup:
        breakup_model = CriticalWeberBreakupModel(
            critical_weber_number=1.0,
            breakup_factor_mean=0.5,
            breakup_factor_max=0.75,
        )
    droplet_solution = solve_droplet_transport(
        gas_solution=gas_solution,
        injection_config=case_config.droplet_injection,
        breakup_model=breakup_model,
    )
    return assemble_simulation_result(
        case_config=case_config,
        gas_solution=gas_solution,
        droplet_solution=droplet_solution,
    )


class TestRuntimeValidationSanityChecks(unittest.TestCase):
    def test_runs_zero_slip_validation_checks(self) -> None:
        simulation_result = _build_result(zero_slip=True, with_breakup=False)
        check_results = run_sanity_checks(simulation_result)
        report = validate_simulation_result(simulation_result)

        self.assertGreaterEqual(len(check_results), 2)
        self.assertTrue(any(result.name == "zero_or_near_zero_slip" for result in check_results))
        self.assertEqual(report.status, "pass")

    def test_runs_breakup_trigger_validation_checks(self) -> None:
        simulation_result = _build_result(zero_slip=False, with_breakup=True)
        check_results = run_sanity_checks(simulation_result)
        report = validate_simulation_result(simulation_result)

        self.assertTrue(any(result.name == "breakup_threshold_behavior" for result in check_results))
        self.assertEqual(report.status, "pass")
        self.assertTrue(any("Triggered breakup" in observation for observation in report.observations))


if __name__ == "__main__":
    unittest.main()