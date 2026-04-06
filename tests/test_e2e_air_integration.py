"""End-to-end air integration workflow test (P22-T03).

Validates the full MVP path from YAML input through gas solver, droplet
transport with breakup, validation, CSV/JSON writing, and profile plotting.
"""

from pathlib import Path
import io
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.app import (
    SimulationRunResult,
    create_application_service,
    run_simulation,
)
from supersonic_atomizer.cli import format_run_report, run_cli


AIR_CASE_YAML = """
fluid:
  working_fluid: air

boundary_conditions:
  Pt_in: 205000.0
  Tt_in: 450.0
  Ps_out: 200000.0

geometry:
  x_start: 0.0
  x_end: 0.1
  n_cells: 5
  area_distribution:
    type: table
    x: [0.0, 0.05, 0.1]
    A: [0.0001, 0.00008, 0.0001]

droplet_injection:
  droplet_velocity_in: 5.0
  droplet_diameter_mean_in: 0.0001
  droplet_diameter_max_in: 0.0002

models:
  breakup_model: weber_critical
  critical_weber_number: 12.0
  breakup_factor_mean: 0.5
  breakup_factor_max: 0.75

outputs:
  output_directory: "{output_dir}"
  write_csv: true
  write_json: true
  generate_plots: true
""".strip()


class TestEndToEndAirIntegration(unittest.TestCase):
    """Full air-case integration from YAML through artifact generation."""

    def _write_case(self, temp_dir: str) -> str:
        """Write an air case YAML to a temp directory and return its path."""
        output_dir = str(Path(temp_dir) / "outputs").replace("\\", "/")
        case_yaml = AIR_CASE_YAML.format(output_dir=output_dir)
        case_path = Path(temp_dir) / "air_case.yaml"
        case_path.write_text(case_yaml, encoding="utf-8")
        return str(case_path)

    def test_full_air_workflow_via_application_service(self) -> None:
        service = create_application_service()

        with tempfile.TemporaryDirectory() as temp_dir:
            case_path = self._write_case(temp_dir)
            result = service.run_simulation(case_path)

            # Status
            self.assertIsInstance(result, SimulationRunResult)
            self.assertEqual(result.status, "completed")
            self.assertIsNotNone(result.simulation_result)

            sim = result.simulation_result

            # Working fluid
            self.assertEqual(sim.working_fluid, "air")

            # Gas solution has physical data
            self.assertGreater(len(sim.gas_solution.states), 0)
            self.assertTrue(all(p > 0 for p in sim.gas_solution.pressure_values))
            self.assertTrue(all(t > 0 for t in sim.gas_solution.temperature_values))
            self.assertTrue(all(rho > 0 for rho in sim.gas_solution.density_values))

            # Droplet solution aligned with gas
            self.assertEqual(len(sim.droplet_solution.states), len(sim.gas_solution.states))
            self.assertEqual(sim.droplet_solution.x_values, sim.gas_solution.x_values)

            # Validation report present
            self.assertIsNotNone(sim.validation_report)
            self.assertGreater(sim.validation_report.checks_run, 0)

            # CSV artifact exists and has content
            self.assertIsNotNone(sim.output_metadata)
            csv_path = Path(sim.output_metadata.csv_path)
            self.assertTrue(csv_path.is_file())
            csv_content = csv_path.read_text(encoding="utf-8")
            self.assertIn("x,", csv_content)
            self.assertIn("pressure", csv_content)
            csv_lines = csv_content.strip().splitlines()
            self.assertEqual(len(csv_lines), len(sim.gas_solution.states) + 1)  # header + data

            # JSON artifact exists and is valid
            json_path = Path(sim.output_metadata.json_path)
            self.assertTrue(json_path.is_file())
            with json_path.open(encoding="utf-8") as f:
                json_data = json.load(f)
            self.assertIn("metadata", json_data)
            self.assertIn("numerical_results", json_data)
            self.assertEqual(json_data["metadata"]["working_fluid"], "air")

            # Plot artifacts exist
            self.assertGreater(len(sim.output_metadata.plot_paths), 0)
            for plot_name, plot_path in sim.output_metadata.plot_paths.items():
                self.assertTrue(Path(plot_path).is_file(), f"Missing plot: {plot_name}")

    def test_full_air_workflow_via_public_entry_point(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            case_path = self._write_case(temp_dir)
            result = run_simulation(case_path)

            self.assertEqual(result.status, "completed")
            self.assertIsNotNone(result.simulation_result)

    def test_full_air_workflow_via_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            case_path = self._write_case(temp_dir)
            stdout = io.StringIO()
            stderr = io.StringIO()

            exit_code = run_cli([case_path], stdout=stdout, stderr=stderr)

            self.assertEqual(exit_code, 0, f"stderr: {stderr.getvalue()}")
            output = stdout.getvalue()
            self.assertIn("Simulation completed", output)
            self.assertIn("air", output)

    def test_missing_case_file_reports_failure(self) -> None:
        result = run_simulation("nonexistent_air_case.yaml")

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.failure_stage, "startup")


if __name__ == "__main__":
    unittest.main()
