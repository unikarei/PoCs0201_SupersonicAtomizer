from pathlib import Path
import unittest


class RunArtifactConventionsTest(unittest.TestCase):
    def test_run_artifact_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        conventions_document = repository_root / "docs" / "run-artifacts.md"

        self.assertTrue(
            conventions_document.is_file(),
            msg="Run artifact conventions document is missing.",
        )

    def test_required_artifact_conventions_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        conventions_document = repository_root / "docs" / "run-artifacts.md"
        contents = conventions_document.read_text(encoding="utf-8")

        required_terms = [
            "outputs/",
            "results.csv",
            "results.json",
            "diagnostics.json",
            "plots/",
            "pressure.png",
            "weber_number.png",
        ]
        missing_terms = [term for term in required_terms if term not in contents]

        self.assertEqual(
            [],
            missing_terms,
            msg=f"Missing required run artifact conventions: {missing_terms}",
        )


if __name__ == "__main__":
    unittest.main()
