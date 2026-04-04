from pathlib import Path
import unittest


class TestPlottingInputContract(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/plotting-input-contract.md").read_text(encoding="utf-8")

        self.assertIn("structured simulation result data", doc)
        self.assertIn("output or plotting settings", doc)
        self.assertIn("does not depend on raw solver internals", doc)
        self.assertIn("does not parse raw YAML", doc)
        self.assertIn("does not recompute physics", doc)
        self.assertIn("figure generation only", doc)


if __name__ == "__main__":
    unittest.main()
