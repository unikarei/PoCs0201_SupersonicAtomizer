from pathlib import Path
import unittest


class TestDropletInjectionAssumptions(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/droplet-injection-assumptions.md").read_text(encoding="utf-8")

        self.assertIn("injection location", doc)
        self.assertIn("initial droplet velocity", doc)
        self.assertIn("initial mean droplet diameter", doc)
        self.assertIn("initial maximum droplet diameter", doc)
        self.assertIn("inlet-side start of the axial domain", doc)
        self.assertIn("maximum diameter should not be smaller than the mean diameter", doc)


if __name__ == "__main__":
    unittest.main()
