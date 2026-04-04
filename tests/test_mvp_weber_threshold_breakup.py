from pathlib import Path
import unittest


class TestMvpWeberThresholdBreakup(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/mvp-weber-threshold-breakup.md").read_text(encoding="utf-8")

        self.assertIn("We > We_{crit}", doc)
        self.assertIn("critical_weber_number", doc)
        self.assertIn("breakup_factor_mean", doc)
        self.assertIn("breakup_factor_max", doc)
        self.assertIn("droplet_mean_diameter", doc)
        self.assertIn("droplet_maximum_diameter", doc)


if __name__ == "__main__":
    unittest.main()
