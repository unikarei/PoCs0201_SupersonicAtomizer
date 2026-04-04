from pathlib import Path
import unittest


class TestGasBoundaryConditionHandling(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/gas-boundary-condition-handling.md").read_text(encoding="utf-8")

        self.assertIn("Pt_in", doc)
        self.assertIn("Tt_in", doc)
        self.assertIn("Ps_out", doc)
        self.assertIn("inlet total pressure", doc)
        self.assertIn("outlet static pressure", doc)
        self.assertIn("invalid or contradictory boundary combinations", doc)


if __name__ == "__main__":
    unittest.main()
