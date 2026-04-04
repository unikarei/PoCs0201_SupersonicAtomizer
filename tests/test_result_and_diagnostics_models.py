from pathlib import Path
import unittest


class ResultAndDiagnosticsModelsTest(unittest.TestCase):
    def test_result_and_diagnostics_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        models_document = repository_root / "docs" / "result-and-diagnostics-models.md"

        self.assertTrue(
            models_document.is_file(),
            msg="Result and diagnostics models document is missing.",
        )

    def test_required_result_model_names_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        models_document = repository_root / "docs" / "result-and-diagnostics-models.md"
        contents = models_document.read_text(encoding="utf-8")

        required_models = [
            "`SimulationResult`",
            "`RunDiagnostics`",
            "`ValidationReport`",
            "`OutputMetadata`",
        ]
        missing_models = [name for name in required_models if name not in contents]

        self.assertEqual(
            [],
            missing_models,
            msg=f"Missing required result/diagnostics model names: {missing_models}",
        )


if __name__ == "__main__":
    unittest.main()
