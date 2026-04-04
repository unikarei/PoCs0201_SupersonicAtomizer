from pathlib import Path
import unittest


class TestBreakupIntegrationSequence(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/breakup-integration-sequence.md").read_text(encoding="utf-8")

        self.assertIn("evaluate slip velocity", doc)
        self.assertIn("evaluate drag response", doc)
        self.assertIn("update droplet velocity", doc)
        self.assertIn("Weber_number", doc)
        self.assertIn("call the breakup model", doc)
        self.assertIn("breakup flag", doc)


if __name__ == "__main__":
    unittest.main()
