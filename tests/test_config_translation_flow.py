from pathlib import Path
import unittest


class ConfigTranslationFlowTest(unittest.TestCase):
    def test_config_translation_flow_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        flow_document = repository_root / "docs" / "config-translation-flow.md"

        self.assertTrue(
            flow_document.is_file(),
            msg="Config translation flow document is missing.",
        )

    def test_required_translation_stages_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        flow_document = repository_root / "docs" / "config-translation-flow.md"
        contents = flow_document.read_text(encoding="utf-8")

        required_stages = [
            "raw parse",
            "schema validation",
            "semantic validation",
            "defaults application",
            "translation into internal models",
        ]
        missing_stages = [stage for stage in required_stages if stage not in contents]

        self.assertEqual(
            [],
            missing_stages,
            msg=f"Missing required config translation stages: {missing_stages}",
        )


if __name__ == "__main__":
    unittest.main()
