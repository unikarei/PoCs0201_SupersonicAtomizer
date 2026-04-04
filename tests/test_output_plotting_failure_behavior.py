from pathlib import Path
import unittest


class TestOutputPlottingFailureBehavior(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/output-plotting-failure-behavior.md").read_text(encoding="utf-8")

        self.assertIn("CSV write failures", doc)
        self.assertIn("JSON write failures", doc)
        self.assertIn("plot-generation failures", doc)
        self.assertIn("distinguishable from solver issues", doc)
        self.assertIn("run summary", doc)
        self.assertIn("partial artifact success", doc)


if __name__ == "__main__":
    unittest.main()
