from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.validation import ValidationCheckResult, assemble_validation_report, run_sanity_checks, validate_simulation_result


class TestRuntimeValidationScaffold(unittest.TestCase):
    def test_exports_validation_runtime_components(self) -> None:
        self.assertEqual(ValidationCheckResult.__name__, "ValidationCheckResult")
        self.assertTrue(callable(run_sanity_checks))
        self.assertTrue(callable(assemble_validation_report))
        self.assertTrue(callable(validate_simulation_result))


if __name__ == "__main__":
    unittest.main()