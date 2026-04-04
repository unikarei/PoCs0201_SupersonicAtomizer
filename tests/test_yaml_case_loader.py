from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.config.loader import load_raw_case_config


class TestYamlCaseLoader(unittest.TestCase):
    def test_loads_valid_yaml_case_mapping(self) -> None:
        case_text = """
fluid:
  working_fluid: air
boundary_conditions:
  Pt_in: 600000.0
  Tt_in: 500.0
  Ps_out: 100000.0
""".strip()

        with tempfile.TemporaryDirectory() as temp_dir:
            case_path = Path(temp_dir) / "case.yaml"
            case_path.write_text(case_text, encoding="utf-8")

            raw_config = load_raw_case_config(case_path)

        self.assertIsInstance(raw_config, dict)
        self.assertEqual(raw_config["fluid"]["working_fluid"], "air")
        self.assertEqual(raw_config["boundary_conditions"]["Pt_in"], 600000.0)

    def test_raises_for_missing_case_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_raw_case_config("missing-case-file.yaml")

    def test_raises_for_invalid_yaml_syntax(self) -> None:
        invalid_yaml = "fluid: [air\n"

        with tempfile.TemporaryDirectory() as temp_dir:
            case_path = Path(temp_dir) / "invalid.yaml"
            case_path.write_text(invalid_yaml, encoding="utf-8")

            with self.assertRaises(ValueError):
                load_raw_case_config(case_path)

    def test_raises_for_non_mapping_top_level_yaml(self) -> None:
        list_yaml = "- fluid\n- boundary_conditions\n"

        with tempfile.TemporaryDirectory() as temp_dir:
            case_path = Path(temp_dir) / "list.yaml"
            case_path.write_text(list_yaml, encoding="utf-8")

            with self.assertRaises(ValueError):
                load_raw_case_config(case_path)


if __name__ == "__main__":
    unittest.main()