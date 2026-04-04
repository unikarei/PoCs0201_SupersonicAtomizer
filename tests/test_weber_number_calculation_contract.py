from pathlib import Path
import unittest


class TestWeberNumberCalculationContract(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/weber-number-calculation-contract.md").read_text(encoding="utf-8")

        self.assertIn("local gas density", doc)
        self.assertIn("slip velocity", doc)
        self.assertIn("dimensionless", doc)
        self.assertIn("SI units", doc)
        self.assertIn("Evaluation Timing", doc)
        self.assertIn("breakup-driving quantity", doc)


if __name__ == "__main__":
    unittest.main()
