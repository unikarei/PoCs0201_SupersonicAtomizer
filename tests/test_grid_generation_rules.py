from pathlib import Path
import unittest


class GridGenerationRulesTest(unittest.TestCase):
    def test_grid_generation_rules_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        rules_document = repository_root / "docs" / "grid-generation-rules.md"

        self.assertTrue(
            rules_document.is_file(),
            msg="Grid generation rules document is missing.",
        )

    def test_required_grid_rule_topics_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        rules_document = repository_root / "docs" / "grid-generation-rules.md"
        contents = rules_document.read_text(encoding="utf-8")

        required_terms = [
            "`x_end` must be greater than `x_start`",
            "`n_cells` must be an integer",
            "`node_count` should therefore be `n_cells + 1`",
            "include both physical domain endpoints",
            "uniform spacing",
            "fail explicitly",
        ]
        missing_terms = [term for term in required_terms if term not in contents]

        self.assertEqual(
            [],
            missing_terms,
            msg=f"Missing required grid generation rule topics: {missing_terms}",
        )


if __name__ == "__main__":
    unittest.main()
