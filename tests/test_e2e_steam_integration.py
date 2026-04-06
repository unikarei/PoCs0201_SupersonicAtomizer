"""End-to-end steam-oriented integration workflow test (P22-T04).

Validates the full MVP path for a steam working-fluid case from YAML input
through gas solver, droplet transport with breakup, validation, and artifact
generation.
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


STEAM_CASE_YAML = """
fluid:
  working_fluid: steam

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
  steam_property_model: equilibrium_mvp

outputs:
  output_directory: "{output_dir}"
  write_csv: true
  write_json: true
  generate_plots: true
""".strip()


class TestEndToEndSteamIntegration(unittest.TestCase):
    """Full steam-case integration from YAML through artifact generation."""

    def _write_case(self, temp_dir: str) -> str:
        """Write a steam case YAML to a temp directory and return its path."""
        output_dir = str(Path(temp_dir) / "outputs").replace("\\", "/")
        case_yaml = STEAM_CASE_YAML.format(output_dir=output_dir)
        case_path = Path(temp_dir) / "steam_case.yaml"
        case_path.write_text(case_yaml, encoding="utf-8")
        return str(case_path)

    def test_full_steam_workflow_via_application_service(self) -> None:
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
            self.assertEqual(sim.working_fluid, "steam")

            # Gas solution has physical data
            self.assertGreater(len(sim.gas_solution.states), 0)
            self.assertTrue(all(p > 0 for p in sim.gas_solution.pressure_values))
            self.assertTrue(all(t > 0 for t in sim.gas_solution.temperature_values))

            # Droplet solution aligned
            self.assertEqual(len(sim.droplet_solution.states), len(sim.gas_solution.states))

            # Validation report present
            self.assertIsNotNone(sim.validation_report)
            self.assertGreater(sim.validation_report.checks_run, 0)

            # CSV artifact
            self.assertIsNotNone(sim.output_metadata)
            csv_path = Path(sim.output_metadata.csv_path)
            self.assertTrue(csv_path.is_file())

            # JSON artifact
            json_path = Path(sim.output_metadata.json_path)
            self.assertTrue(json_path.is_file())
            with json_path.open(encoding="utf-8") as f:
                json_data = json.load(f)
            self.assertEqual(json_data["metadata"]["working_fluid"], "steam")

            # Plot artifacts
            self.assertGreater(len(sim.output_metadata.plot_paths), 0)
            for plot_name, plot_path in sim.output_metadata.plot_paths.items():
                self.assertTrue(Path(plot_path).is_file(), f"Missing plot: {plot_name}")

    def test_full_steam_workflow_via_public_entry_point(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            case_path = self._write_case(temp_dir)
            result = run_simulation(case_path)

            self.assertEqual(result.status, "completed")
            self.assertIsNotNone(result.simulation_result)
            self.assertEqual(result.simulation_result.working_fluid, "steam")

    def test_full_steam_workflow_via_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            case_path = self._write_case(temp_dir)
            stdout = io.StringIO()
            stderr = io.StringIO()

            exit_code = run_cli([case_path], stdout=stdout, stderr=stderr)

            self.assertEqual(exit_code, 0, f"stderr: {stderr.getvalue()}")
            output = stdout.getvalue()
            self.assertIn("Simulation completed", output)
            self.assertIn("steam", output)

    def test_steam_settings_recorded_in_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            case_path = self._write_case(temp_dir)
            service = create_application_service()
            result = service.run_simulation(case_path)

            self.assertEqual(result.status, "completed")
            json_path = Path(result.simulation_result.output_metadata.json_path)
            with json_path.open(encoding="utf-8") as f:
                json_data = json.load(f)

            settings = json_data.get("settings_summary", {})
            self.assertEqual(settings.get("fluid", {}).get("working_fluid"), "steam")
            self.assertEqual(
                settings.get("models", {}).get("steam_property_model"),
                "equilibrium_mvp",
            )


if __name__ == "__main__":
    unittest.main()
