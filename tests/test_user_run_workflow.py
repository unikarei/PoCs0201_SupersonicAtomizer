from pathlib import Path
import unittest


class TestUserRunWorkflow(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/user-run-workflow.md").read_text(encoding="utf-8")

        self.assertIn("prepare a YAML case file", doc)
        self.assertIn("run the simulator from the CLI", doc)
        self.assertIn("CSV", doc)
        self.assertIn("JSON", doc)
        self.assertIn("plot artifacts", doc)
        self.assertIn("run status", doc)


if __name__ == "__main__":
    unittest.main()
