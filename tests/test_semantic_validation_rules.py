from pathlib import Path
import unittest


class SemanticValidationRulesTest(unittest.TestCase):
    def test_semantic_validation_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        validation_document = repository_root / "docs" / "semantic-validation.md"

        self.assertTrue(
            validation_document.is_file(),
            msg="Semantic validation rules document is missing.",
        )

    def test_required_validation_topics_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        validation_document = repository_root / "docs" / "semantic-validation.md"
        contents = validation_document.read_text(encoding="utf-8")

        required_terms = [
            "required",
            "air or `steam`",
            "SI units",
            "strictly positive",
            "droplet_diameter_mean_in",
            "droplet_diameter_max_in",
            "x_end",
            "x_start",
            "n_cells",
            "same length",
            "strictly increasing",
            "area_distribution.A",
        ]
        missing_terms = [term for term in required_terms if term not in contents]

        self.assertEqual(
            [],
            missing_terms,
            msg=f"Missing required semantic validation topics: {missing_terms}",
        )


if __name__ == "__main__":
    unittest.main()
