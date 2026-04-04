from pathlib import Path
import unittest


class TestAssumptionsLimitationsSummary(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/assumptions-limitations-summary.md").read_text(encoding="utf-8")

        self.assertIn("quasi-1D internal flow", doc)
        self.assertIn("one-way coupling", doc)
        self.assertIn("simple Weber-threshold breakup", doc)
        self.assertIn("3D CFD", doc)
        self.assertIn("wall-film physics", doc)
        self.assertIn("non-equilibrium condensation", doc)


if __name__ == "__main__":
    unittest.main()
