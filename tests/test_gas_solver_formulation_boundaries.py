from pathlib import Path
import unittest


class TestGasSolverFormulationBoundaries(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/gas-solver-formulation-boundaries.md").read_text(encoding="utf-8")

        self.assertIn("steady quasi-1D internal compressible flow", doc)
        self.assertIn("prescribed one-dimensional geometry", doc)
        self.assertIn("one-way coupling", doc)
        self.assertIn("2D or 3D CFD", doc)
        self.assertIn("high-fidelity turbulence", doc)
        self.assertIn("non-equilibrium condensation", doc)


if __name__ == "__main__":
    unittest.main()
