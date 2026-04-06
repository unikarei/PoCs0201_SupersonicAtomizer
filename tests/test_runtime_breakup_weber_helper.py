from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.breakup import evaluate_weber_number
from supersonic_atomizer.common import NumericalError


class TestRuntimeBreakupWeberHelper(unittest.TestCase):
    def test_returns_zero_for_zero_slip(self) -> None:
        self.assertEqual(
            evaluate_weber_number(
                gas_density=1.2,
                slip_velocity=0.0,
                reference_diameter=1.0e-4,
            ),
            0.0,
        )

    def test_returns_positive_value_for_breakup_driving_conditions(self) -> None:
        weber_number = evaluate_weber_number(
            gas_density=1.2,
            slip_velocity=50.0,
            reference_diameter=1.0e-4,
        )

        self.assertGreater(weber_number, 1.0)

    def test_rejects_invalid_inputs(self) -> None:
        with self.assertRaises(NumericalError):
            evaluate_weber_number(gas_density=0.0, slip_velocity=10.0, reference_diameter=1.0e-4)


if __name__ == "__main__":
    unittest.main()