from pathlib import Path
import unittest


class SolverStateModelsTest(unittest.TestCase):
    def test_solver_state_models_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        models_document = repository_root / "docs" / "solver-state-models.md"

        self.assertTrue(
            models_document.is_file(),
            msg="Solver state models document is missing.",
        )

    def test_required_solver_state_model_names_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        models_document = repository_root / "docs" / "solver-state-models.md"
        contents = models_document.read_text(encoding="utf-8")

        required_models = [
            "`ThermoState`",
            "`GasState`",
            "`GasSolution`",
            "`DropletState`",
            "`DropletSolution`",
            "`BreakupDecision`",
        ]
        missing_models = [name for name in required_models if name not in contents]

        self.assertEqual(
            [],
            missing_models,
            msg=f"Missing required solver state model names: {missing_models}",
        )


if __name__ == "__main__":
    unittest.main()
