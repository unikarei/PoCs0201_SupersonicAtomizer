from pathlib import Path
import unittest


class TestDragModelAbstraction(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/drag-model-abstraction.md").read_text(encoding="utf-8")

        self.assertIn("replaceable", doc)
        self.assertIn("simple spherical drag model", doc)
        self.assertIn("configuration", doc)
        self.assertIn("alternate drag correlations", doc)
        self.assertIn("deterministic output", doc)


if __name__ == "__main__":
    unittest.main()
