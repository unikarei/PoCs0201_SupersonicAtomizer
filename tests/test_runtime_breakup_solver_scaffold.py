from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.breakup import (
    BreakupModel,
    BreakupModelInputs,
    CriticalWeberBreakupModel,
    evaluate_weber_number,
)
from supersonic_atomizer.domain import ModelSelectionConfig


class TestRuntimeBreakupSolverScaffold(unittest.TestCase):
    def test_exports_runtime_breakup_components(self) -> None:
        self.assertTrue(issubclass(CriticalWeberBreakupModel, BreakupModel))
        self.assertTrue(callable(evaluate_weber_number))
        self.assertIn("BreakupModelInputs", BreakupModelInputs.__name__)

    def test_model_selection_config_defaults_remain_breakup_compatible(self) -> None:
        model_config = ModelSelectionConfig()
        self.assertEqual(model_config.breakup_model, "weber_critical")


if __name__ == "__main__":
    unittest.main()