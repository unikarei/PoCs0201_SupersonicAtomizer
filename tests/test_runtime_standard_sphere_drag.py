from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.common import ConfigurationError
from supersonic_atomizer.solvers.droplet import (
    DragEvaluation,
    StandardSphereDragInputs,
    StandardSphereDragModel,
)


class TestRuntimeStandardSphereDrag(unittest.TestCase):
    def test_evaluates_representative_drag_inputs(self) -> None:
        drag_evaluation = StandardSphereDragModel().evaluate(
            StandardSphereDragInputs(
                gas_density=1.2,
                slip_velocity=20.0,
                droplet_diameter=1.0e-4,
            )
        )

        self.assertIsInstance(drag_evaluation, DragEvaluation)
        self.assertGreater(drag_evaluation.reynolds_number, 0.0)
        self.assertGreater(drag_evaluation.drag_coefficient, 0.0)
        self.assertGreater(drag_evaluation.acceleration, 0.0)

    def test_zero_slip_returns_zero_drag_response(self) -> None:
        drag_evaluation = StandardSphereDragModel().evaluate(
            StandardSphereDragInputs(
                gas_density=1.2,
                slip_velocity=0.0,
                droplet_diameter=1.0e-4,
            )
        )

        self.assertEqual(drag_evaluation.reynolds_number, 0.0)
        self.assertEqual(drag_evaluation.drag_coefficient, 0.0)
        self.assertEqual(drag_evaluation.acceleration, 0.0)

    def test_rejects_invalid_drag_inputs(self) -> None:
        with self.assertRaises(ConfigurationError):
            StandardSphereDragModel().evaluate(
                StandardSphereDragInputs(
                    gas_density=-1.0,
                    slip_velocity=20.0,
                    droplet_diameter=1.0e-4,
                )
            )


if __name__ == "__main__":
    unittest.main()