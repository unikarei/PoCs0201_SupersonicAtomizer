from pathlib import Path
import unittest


class TestGasOnlyValidationCases(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/gas-only-validation-cases.md").read_text(encoding="utf-8")

        self.assertIn("Constant-Area Gas-Only Case", doc)
        self.assertIn("Converging/Diverging Geometry Sanity Case", doc)
        self.assertIn("gas only", doc)
        self.assertIn("no droplet transport enabled", doc)
        self.assertIn("pass/warn/fail status", doc)
        self.assertIn("qualitative trend", doc)


if __name__ == "__main__":
    unittest.main()
