from pathlib import Path
import unittest


class TestUnitTestMatrix(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/unit-test-matrix.md").read_text(encoding="utf-8")

        self.assertIn("config validation", doc)
        self.assertIn("geometry interpolation", doc)
        self.assertIn("grid generation", doc)
        self.assertIn("thermo contracts", doc)
        self.assertIn("Weber number evaluation", doc)
        self.assertIn("output formatting", doc)


if __name__ == "__main__":
    unittest.main()
