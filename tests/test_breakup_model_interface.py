from pathlib import Path
import unittest


class TestBreakupModelInterface(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/breakup-model-interface.md").read_text(encoding="utf-8")

        self.assertIn("local gas-state context", doc)
        self.assertIn("local droplet-state context", doc)
        self.assertIn("critical Weber number", doc)
        self.assertIn("updated mean droplet diameter", doc)
        self.assertIn("updated maximum droplet diameter", doc)
        self.assertIn("BreakupDecision", doc)


if __name__ == "__main__":
    unittest.main()
