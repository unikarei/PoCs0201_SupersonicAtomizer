from pathlib import Path
import unittest


class TestGasSolverSequence(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/gas-solver-sequence.md").read_text(encoding="utf-8")

        self.assertIn("receive validated inputs", doc)
        self.assertIn("initialize inlet-side state representation", doc)
        self.assertIn("advance or assemble gas states", doc)
        self.assertIn("Mach number", doc)
        self.assertIn("GasSolution", doc)
        self.assertIn("diagnostics", doc)


if __name__ == "__main__":
    unittest.main()
