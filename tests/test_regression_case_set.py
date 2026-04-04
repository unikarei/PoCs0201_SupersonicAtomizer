from pathlib import Path
import unittest


class TestRegressionCaseSet(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/regression-case-set.md").read_text(encoding="utf-8")

        self.assertIn("constant-area gas-only case", doc)
        self.assertIn("converging/diverging gas-only sanity case", doc)
        self.assertIn("zero-slip or near-zero-slip droplet case", doc)
        self.assertIn("breakup-trigger case", doc)
        self.assertIn("qualitative trend descriptions", doc)
        self.assertIn("tolerances", doc)


if __name__ == "__main__":
    unittest.main()
