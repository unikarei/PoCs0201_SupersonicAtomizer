from pathlib import Path
import unittest


class TestExampleYamlConventions(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/example-yaml-conventions.md").read_text(encoding="utf-8")

        self.assertIn("working_fluid", doc)
        self.assertIn("Pt_in", doc)
        self.assertIn("Tt_in", doc)
        self.assertIn("Ps_out", doc)
        self.assertIn("inlet_wetness", doc)
        self.assertIn("breakup model selection", doc)


if __name__ == "__main__":
    unittest.main()
