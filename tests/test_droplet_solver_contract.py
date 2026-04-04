from pathlib import Path
import unittest


class TestDropletSolverContract(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/droplet-solver-contract.md").read_text(encoding="utf-8")

        self.assertIn("AxialGrid", doc)
        self.assertIn("GasSolution", doc)
        self.assertIn("DropletInjectionConfig", doc)
        self.assertIn("droplet_velocity", doc)
        self.assertIn("slip_velocity", doc)
        self.assertIn("droplet_mean_diameter", doc)
        self.assertIn("droplet_maximum_diameter", doc)
        self.assertIn("Weber_number", doc)


if __name__ == "__main__":
    unittest.main()
