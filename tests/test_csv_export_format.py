from pathlib import Path
import unittest


class TestCsvExportFormat(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/csv-export-format.md").read_text(encoding="utf-8")

        self.assertIn("x", doc)
        self.assertIn("A", doc)
        self.assertIn("pressure", doc)
        self.assertIn("working_fluid_velocity", doc)
        self.assertIn("droplet_mean_diameter", doc)
        self.assertIn("stable documented column order", doc)
        self.assertIn("run-artifact conventions", doc)


if __name__ == "__main__":
    unittest.main()
