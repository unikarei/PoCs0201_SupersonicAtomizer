from pathlib import Path
import unittest


class TestIntegrationTestMatrix(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/integration-test-matrix.md").read_text(encoding="utf-8")

        self.assertIn("YAML-to-Result Execution", doc)
        self.assertIn("Air Case Pipeline", doc)
        self.assertIn("Steam-Provider Selection Behavior", doc)
        self.assertIn("Output Generation", doc)
        self.assertIn("deterministic", doc)
        self.assertIn("manual inspection", doc)


if __name__ == "__main__":
    unittest.main()
