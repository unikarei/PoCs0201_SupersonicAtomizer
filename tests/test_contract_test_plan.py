from pathlib import Path
import unittest


class TestContractTestPlan(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/contract-test-plan.md").read_text(encoding="utf-8")

        self.assertIn("Thermo Providers", doc)
        self.assertIn("Breakup Models", doc)
        self.assertIn("interface contracts", doc)
        self.assertIn("invalid-state handling is explicit", doc)
        self.assertIn("unsupported or invalid inputs fail explicitly", doc)


if __name__ == "__main__":
    unittest.main()
