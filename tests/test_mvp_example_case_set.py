from pathlib import Path
import unittest


class TestMvpExampleCaseSet(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/mvp-example-case-set.md").read_text(encoding="utf-8")

        self.assertIn("one air case", doc)
        self.assertIn("one steam-oriented case", doc)
        self.assertIn("working fluid selection as air", doc)
        self.assertIn("working fluid selection as steam", doc)
        self.assertIn("IF97-ready", doc)


if __name__ == "__main__":
    unittest.main()
