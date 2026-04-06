from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.validation import ValidationCheckResult, assemble_validation_report


class TestRuntimeValidationReporting(unittest.TestCase):
    def test_assembles_counts_and_status(self) -> None:
        report = assemble_validation_report(
            (
                ValidationCheckResult(name="check_a", status="pass", observation="a ok"),
                ValidationCheckResult(name="check_b", status="warn", observation="b warn"),
                ValidationCheckResult(name="check_c", status="fail", observation="c fail"),
            )
        )

        self.assertEqual(report.status, "fail")
        self.assertEqual(report.checks_run, 3)
        self.assertEqual(report.checks_passed, 1)
        self.assertEqual(report.checks_warned, 1)
        self.assertEqual(report.checks_failed, 1)


if __name__ == "__main__":
    unittest.main()