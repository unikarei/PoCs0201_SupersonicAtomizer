from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.app import assemble_simulation_result
from supersonic_atomizer.common import OutputError
from supersonic_atomizer.domain import BoundaryConditionConfig, CaseConfig, DropletInjectionConfig, FluidConfig, GeometryConfig, ModelSelectionConfig, OutputConfig
from supersonic_atomizer.geometry import build_geometry_model
from supersonic_atomizer.io import build_output_metadata
from supersonic_atomizer.plotting import generate_profile_plots
from supersonic_atomizer.solvers.droplet import solve_droplet_transport
from supersonic_atomizer.solvers.gas import solve_quasi_1d_gas_flow
from supersonic_atomizer.thermo import AirThermoProvider


def _make_result(temp_dir: str | None = None):
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
        outputs=OutputConfig(output_directory=temp_dir or "outputs", generate_plots=True),
        case_name="plot_case",
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
    output_metadata = build_output_metadata(output_config=case_config.outputs, run_id="run-fixed")
    return assemble_simulation_result(
        case_config=case_config,
        gas_solution=gas_solution,
        droplet_solution=droplet_solution,
        output_metadata=output_metadata,
    )


class TestRuntimePlotProfiles(unittest.TestCase):
    def test_generates_required_mvp_plot_set(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            simulation_result = _make_result(temp_dir)
            plot_paths = generate_profile_plots(simulation_result)

            self.assertEqual(len(plot_paths), 8)
            self.assertTrue(Path(plot_paths["pressure"]).is_file())
            self.assertTrue(Path(plot_paths["weber_number"]).is_file())

    def test_requires_plot_output_metadata(self) -> None:
        simulation_result = _make_result()
        simulation_result = simulation_result.__class__(
            case_name=simulation_result.case_name,
            working_fluid=simulation_result.working_fluid,
            gas_solution=simulation_result.gas_solution,
            droplet_solution=simulation_result.droplet_solution,
            diagnostics=simulation_result.diagnostics,
            settings_summary=simulation_result.settings_summary,
            validation_report=simulation_result.validation_report,
            output_metadata=None,
        )

        with self.assertRaises(OutputError):
            generate_profile_plots(simulation_result)


if __name__ == "__main__":
    unittest.main()