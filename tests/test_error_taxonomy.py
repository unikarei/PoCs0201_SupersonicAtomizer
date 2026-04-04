from pathlib import Path
import unittest


class ErrorTaxonomyTest(unittest.TestCase):
    def test_error_taxonomy_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        taxonomy_document = repository_root / "docs" / "error-taxonomy.md"

        self.assertTrue(
            taxonomy_document.is_file(),
            msg="Error taxonomy document is missing.",
        )

    def test_required_error_categories_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        taxonomy_document = repository_root / "docs" / "error-taxonomy.md"
        contents = taxonomy_document.read_text(encoding="utf-8")

        required_categories = [
            "Input Parsing Errors",
            "Configuration Errors",
            "Model-Selection Errors",
            "Thermo Errors",
            "Numerical Errors",
            "Output Errors",
            "Validation Errors",
        ]
        missing_categories = [
            category for category in required_categories if category not in contents
        ]

        self.assertEqual(
            [],
            missing_categories,
            msg=f"Missing required error categories: {missing_categories}",
        )


if __name__ == "__main__":
    unittest.main()
