from pathlib import Path
import unittest


class TestBreakupValidationCases(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/breakup-validation-cases.md").read_text(encoding="utf-8")

        self.assertIn("No-Breakup Case", doc)
        self.assertIn("Breakup-Trigger Case", doc)
        self.assertIn("below the critical threshold", doc)
        self.assertIn("exceeds the critical threshold", doc)
        self.assertIn("diameter metrics remain unchanged", doc)
        self.assertIn("mean and maximum diameters decrease", doc)


if __name__ == "__main__":
    unittest.main()
