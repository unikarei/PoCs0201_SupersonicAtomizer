from pathlib import Path
import unittest


class CaseConfigurationModelsTest(unittest.TestCase):
    def test_case_configuration_models_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        models_document = repository_root / "docs" / "case-configuration-models.md"

        self.assertTrue(
            models_document.is_file(),
            msg="Case configuration models document is missing.",
        )

    def test_required_configuration_model_names_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        models_document = repository_root / "docs" / "case-configuration-models.md"
        contents = models_document.read_text(encoding="utf-8")

        required_models = [
            "`CaseConfig`",
            "`FluidConfig`",
            "`BoundaryConditionConfig`",
            "`GeometryConfig`",
            "`DropletInjectionConfig`",
            "`ModelSelectionConfig`",
            "`OutputConfig`",
        ]
        missing_models = [name for name in required_models if name not in contents]

        self.assertEqual(
            [],
            missing_models,
            msg=f"Missing required configuration model names: {missing_models}",
        )


if __name__ == "__main__":
    unittest.main()
