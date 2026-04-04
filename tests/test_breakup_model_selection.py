from pathlib import Path
import unittest


class TestBreakupModelSelection(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/breakup-model-selection.md").read_text(encoding="utf-8")

        self.assertIn("configuration-driven", doc)
        self.assertIn("Weber-threshold", doc)
        self.assertIn("unsupported breakup-model names", doc)
        self.assertIn("registry", doc)
        self.assertIn("must not fall back silently", doc)


if __name__ == "__main__":
    unittest.main()
