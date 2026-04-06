from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.domain import OutputConfig
from supersonic_atomizer.io import build_output_metadata, ensure_output_directories


class TestRuntimeOutputPaths(unittest.TestCase):
    def test_builds_expected_artifact_metadata(self) -> None:
        output_metadata = build_output_metadata(
            output_config=OutputConfig(output_directory="outputs", write_csv=True, write_json=True, generate_plots=True),
            run_id="run-fixed",
        )

        self.assertEqual(output_metadata.output_directory, str(Path("outputs") / "run-fixed"))
        self.assertTrue(output_metadata.csv_path.endswith("results.csv"))
        self.assertTrue(output_metadata.json_path.endswith("results.json"))
        self.assertIn("pressure", output_metadata.plot_paths)
        self.assertTrue(output_metadata.plot_paths["weber_number"].endswith("weber_number.png"))

    def test_creates_output_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_metadata = build_output_metadata(
                output_config=OutputConfig(output_directory=temp_dir, write_csv=True, write_json=True, generate_plots=True),
                run_id="run-fixed",
            )

            ensure_output_directories(output_metadata)

            self.assertTrue(Path(output_metadata.output_directory).is_dir())
            self.assertTrue(Path(next(iter(output_metadata.plot_paths.values()))).parent.is_dir())


if __name__ == "__main__":
    unittest.main()