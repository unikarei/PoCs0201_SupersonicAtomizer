from pathlib import Path
import unittest


class TestSlipVelocityDragEvaluationFlow(unittest.TestCase):
    def test_required_content_present(self) -> None:
        doc = Path("docs/slip-velocity-drag-evaluation-flow.md").read_text(encoding="utf-8")

        self.assertIn("Gas-State Lookup", doc)
        self.assertIn("Slip-Velocity Evaluation", doc)
        self.assertIn("Drag Input Preparation", doc)
        self.assertIn("Drag Evaluation", doc)
        self.assertIn("Droplet Motion Update", doc)
        self.assertIn("gas velocity and droplet velocity", doc)


if __name__ == "__main__":
    unittest.main()
