from pathlib import Path
import unittest


class DevelopmentToolingBaselineTest(unittest.TestCase):
    def test_tooling_baseline_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        tooling_document = repository_root / "docs" / "development-tooling.md"

        self.assertTrue(
            tooling_document.is_file(),
            msg="Development tooling baseline document is missing.",
        )

    def test_tooling_baseline_documents_required_tools(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        tooling_document = repository_root / "docs" / "development-tooling.md"
        contents = tooling_document.read_text(encoding="utf-8")

        required_terms = ["Python 3.11", "venv", "pip", "unittest", "ruff", "black", "VS Code"]
        missing_terms = [term for term in required_terms if term not in contents]

        self.assertEqual(
            [],
            missing_terms,
            msg=f"Missing required tooling decisions in document: {missing_terms}",
        )


if __name__ == "__main__":
    unittest.main()
