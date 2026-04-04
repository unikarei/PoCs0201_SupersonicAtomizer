from pathlib import Path
import unittest


class TestJsonExportFormat(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/json-export-format.md").read_text(encoding="utf-8")

        self.assertIn("metadata", doc)
        self.assertIn("settings summary", doc)
        self.assertIn("numerical results", doc)
        self.assertIn("diagnostics", doc)
        self.assertIn("working_fluid_velocity", doc)
        self.assertIn("droplet_maximum_diameter", doc)
        self.assertIn("machine-readable", doc)


if __name__ == "__main__":
    unittest.main()
