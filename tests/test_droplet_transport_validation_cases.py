from pathlib import Path
import unittest


class TestDropletTransportValidationCases(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/droplet-transport-validation-cases.md").read_text(encoding="utf-8")

        self.assertIn("Zero-Slip or Near-Zero-Slip Case", doc)
        self.assertIn("Slip-Driven Acceleration Case", doc)
        self.assertIn("drag-driven acceleration", doc)
        self.assertIn("breakup effects not required", doc)
        self.assertIn("pass/warn/fail status", doc)
        self.assertIn("qualitative trend", doc)


if __name__ == "__main__":
    unittest.main()
