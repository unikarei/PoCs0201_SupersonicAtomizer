from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.app import SimulationRunResult, create_application_service, run_simulation


def _build_case_yaml(*, working_fluid: str = "air") -> str:
	steam_backend = "\n  steam_property_model: equilibrium_mvp" if working_fluid == "steam" else ""
	return f"""
fluid:
  working_fluid: {working_fluid}
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
  breakup_factor_mean: 0.5
  breakup_factor_max: 0.75{steam_backend}
outputs:
  output_directory: outputs
  write_csv: true
  write_json: true
  generate_plots: true
""".strip()


class TestRuntimeFullApplicationService(unittest.TestCase):
	def test_application_service_runs_full_air_workflow(self) -> None:
		service = create_application_service()
		case_yaml = _build_case_yaml(working_fluid="air")

		with tempfile.TemporaryDirectory() as temporary_directory:
			case_path = Path(temporary_directory) / "air_case.yaml"
			case_path.write_text(case_yaml, encoding="utf-8")

			run_result = service.run_simulation(str(case_path))

		self.assertIsInstance(run_result, SimulationRunResult)
		self.assertEqual(run_result.status, "completed")
		self.assertIsNotNone(run_result.simulation_result)
		self.assertEqual(run_result.simulation_result.working_fluid, "air")
		self.assertIsNotNone(run_result.simulation_result.validation_report)
		self.assertTrue(Path(run_result.simulation_result.output_metadata.csv_path).is_file())
		self.assertTrue(Path(run_result.simulation_result.output_metadata.json_path).is_file())
		self.assertTrue(Path(run_result.simulation_result.output_metadata.plot_paths["pressure"]).is_file())

	def test_default_run_simulation_entry_point_executes_full_workflow(self) -> None:
		case_yaml = _build_case_yaml(working_fluid="air")

		with tempfile.TemporaryDirectory() as temporary_directory:
			case_path = Path(temporary_directory) / "air_case.yaml"
			case_path.write_text(case_yaml, encoding="utf-8")

			run_result = run_simulation(str(case_path))

		self.assertEqual(run_result.status, "completed")

	def test_application_service_reports_startup_failures_through_full_run_result(self) -> None:
		service = create_application_service()

		run_result = service.run_simulation("missing_case.yaml")

		self.assertEqual(run_result.status, "failed")
		self.assertEqual(run_result.failure_stage, "startup")
		self.assertIsNone(run_result.simulation_result)


if __name__ == "__main__":
	unittest.main()