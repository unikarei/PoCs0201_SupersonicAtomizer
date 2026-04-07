from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.app import LavalSweepResult, run_laval_nozzle_back_pressure_sweep


class TestRuntimeLavalNozzleSweep(unittest.TestCase):
    def test_runs_laval_nozzle_back_pressure_sweep_and_writes_artifacts(self) -> None:
        case_path = Path(__file__).resolve().parents[1] / "examples" / "laval_nozzle_air.yaml"

        with tempfile.TemporaryDirectory() as temporary_directory:
            result = run_laval_nozzle_back_pressure_sweep(
                case_path=str(case_path),
                output_directory=temporary_directory,
            )

            self.assertIsInstance(result, LavalSweepResult)
            self.assertEqual([curve.label for curve in result.curves], ["b", "d", "g", "h", "j", "k"])
            self.assertTrue(Path(result.plot_path).is_file())
            self.assertTrue(Path(result.summary_path).is_file())
            self.assertTrue(Path(result.report_path).is_file())
            self.assertEqual(result.validation_status, "pass")
            self.assertTrue(any("expected ordering" in observation for observation in result.validation_observations))
            branch_map = {curve.label: curve.selected_branch for curve in result.curves}
            self.assertEqual(branch_map["b"], "subsonic_internal")
            self.assertEqual(branch_map["d"], "exit_normal_shock")
            self.assertEqual(branch_map["j"], "fully_supersonic_internal")
            self.assertEqual(branch_map["k"], "fully_supersonic_internal")
            self.assertAlmostEqual(
                result.curves[4].pressure_ratio_values[-1],
                result.curves[5].pressure_ratio_values[-1],
                places=8,
            )


if __name__ == "__main__":
    unittest.main()
