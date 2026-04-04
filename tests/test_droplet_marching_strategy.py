from pathlib import Path
import unittest


class TestDropletMarchingStrategy(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/droplet-marching-strategy.md").read_text(encoding="utf-8")

        self.assertIn("same axial grid used by the gas solution", doc)
        self.assertIn("evaluate slip velocity", doc)
        self.assertIn("update droplet velocity", doc)
        self.assertIn("Weber number", doc)
        self.assertIn("DropletState", doc)
        self.assertIn("axial order", doc)


if __name__ == "__main__":
    unittest.main()
