from pathlib import Path
import unittest


class TestGasDiagnosticsFailureCriteria(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/gas-diagnostics-failure-criteria.md").read_text(encoding="utf-8")

        self.assertIn("Nonphysical State Diagnostics", doc)
        self.assertIn("Branch Ambiguity Diagnostics", doc)
        self.assertIn("Failed Closure Diagnostics", doc)
        self.assertIn("Incomplete Solution Progression Diagnostics", doc)
        self.assertIn("axial location", doc)
        self.assertIn("last valid state summary", doc)


if __name__ == "__main__":
    unittest.main()
