from pathlib import Path
import unittest


class TestTestDataOrganization(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/test-data-organization.md").read_text(encoding="utf-8")

        self.assertIn("unit fixtures", doc)
        self.assertIn("integration cases", doc)
        self.assertIn("regression references", doc)
        self.assertIn("validation artifacts", doc)
        self.assertIn("air and steam cases", doc)
        self.assertIn("should not leak into solver logic", doc)


if __name__ == "__main__":
    unittest.main()
