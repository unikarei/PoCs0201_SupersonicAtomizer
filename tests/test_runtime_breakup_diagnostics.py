from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.breakup import validate_breakup_decision
from supersonic_atomizer.common import NumericalError
from supersonic_atomizer.domain import BreakupDecision


class TestRuntimeBreakupDiagnostics(unittest.TestCase):
    def test_rejects_invalid_updated_diameter_ordering(self) -> None:
        with self.assertRaises(NumericalError):
            validate_breakup_decision(
                BreakupDecision(
                    triggered=True,
                    weber_number=20.0,
                    critical_weber_number=12.0,
                    updated_mean_diameter=1.0e-4,
                    updated_maximum_diameter=5.0e-5,
                )
            )


if __name__ == "__main__":
    unittest.main()