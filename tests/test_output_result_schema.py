from pathlib import Path
import unittest


class TestOutputResultSchema(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/output-result-schema.md").read_text(encoding="utf-8")

        self.assertIn("SimulationResult", doc)
        self.assertIn("x", doc)
        self.assertIn("A", doc)
        self.assertIn("pressure", doc)
        self.assertIn("droplet_velocity", doc)
        self.assertIn("Weber_number", doc)
        self.assertIn("breakup event indicator", doc)
        self.assertIn("diagnostics", doc)


if __name__ == "__main__":
    unittest.main()
