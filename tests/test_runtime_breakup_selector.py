from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.breakup import CriticalWeberBreakupModel, select_breakup_model
from supersonic_atomizer.common import ConfigurationError, ModelSelectionError
from supersonic_atomizer.domain import ModelSelectionConfig


class TestRuntimeBreakupSelector(unittest.TestCase):
    def test_selects_supported_weber_breakup_model(self) -> None:
        breakup_model = select_breakup_model(
            ModelSelectionConfig(
                breakup_model="weber_critical",
                critical_weber_number=10.0,
                breakup_factor_mean=0.5,
                breakup_factor_max=0.75,
            )
        )

        self.assertIsInstance(breakup_model, CriticalWeberBreakupModel)
        self.assertEqual(breakup_model.model_name, "weber_critical")

    def test_rejects_unsupported_breakup_model_name(self) -> None:
        with self.assertRaises(ModelSelectionError):
            select_breakup_model(
                ModelSelectionConfig(
                    breakup_model="unsupported_model",
                    breakup_factor_mean=0.5,
                    breakup_factor_max=0.75,
                )
            )

    def test_requires_explicit_breakup_reduction_factors(self) -> None:
        with self.assertRaises(ConfigurationError):
            select_breakup_model(ModelSelectionConfig(breakup_model="weber_critical"))


if __name__ == "__main__":
    unittest.main()