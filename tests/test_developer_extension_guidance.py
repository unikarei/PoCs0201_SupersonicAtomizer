from pathlib import Path
import unittest


class TestDeveloperExtensionGuidance(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/developer-extension-guidance.md").read_text(encoding="utf-8")

        self.assertIn("thermo extensions", doc)
        self.assertIn("breakup-model extensions", doc)
        self.assertIn("validation-case extensions", doc)
        self.assertIn("thermo interface contract", doc)
        self.assertIn("breakup-model interface", doc)
        self.assertIn("small, testable changes", doc)


if __name__ == "__main__":
    unittest.main()
