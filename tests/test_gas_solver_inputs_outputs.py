from pathlib import Path
import unittest


class TestGasSolverInputsOutputs(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/gas-solver-inputs-outputs.md").read_text(encoding="utf-8")

        self.assertIn("AxialGrid", doc)
        self.assertIn("GeometryModel", doc)
        self.assertIn("Pt_in", doc)
        self.assertIn("Tt_in", doc)
        self.assertIn("Ps_out", doc)
        self.assertIn("pressure", doc)
        self.assertIn("temperature", doc)
        self.assertIn("density", doc)
        self.assertIn("velocity", doc)
        self.assertIn("mach_number", doc)


if __name__ == "__main__":
    unittest.main()
