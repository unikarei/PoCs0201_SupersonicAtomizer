from pathlib import Path
import unittest


class TestMvpPlotSet(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/mvp-plot-set.md").read_text(encoding="utf-8")

        self.assertIn("pressure", doc)
        self.assertIn("temperature", doc)
        self.assertIn("working fluid velocity", doc)
        self.assertIn("droplet velocity", doc)
        self.assertIn("Mach number", doc)
        self.assertIn("droplet mean diameter", doc)
        self.assertIn("Weber number", doc)


if __name__ == "__main__":
    unittest.main()
