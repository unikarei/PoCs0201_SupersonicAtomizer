from pathlib import Path
import unittest


class TestDropletDiagnosticsBoundsChecks(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/droplet-diagnostics-bounds-checks.md").read_text(encoding="utf-8")

        self.assertIn("negative droplet velocity", doc)
        self.assertIn("nonpositive mean droplet diameter", doc)
        self.assertIn("nonpositive maximum droplet diameter", doc)
        self.assertIn("NaN or infinite", doc)
        self.assertIn("invalid Weber number", doc)
        self.assertIn("last valid droplet state summary", doc)


if __name__ == "__main__":
    unittest.main()
