from pathlib import Path
import unittest


class AxialGridModelTest(unittest.TestCase):
    def test_axial_grid_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        grid_document = repository_root / "docs" / "axial-grid-model.md"

        self.assertTrue(
            grid_document.is_file(),
            msg="Axial grid model document is missing.",
        )

    def test_required_grid_concepts_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        grid_document = repository_root / "docs" / "axial-grid-model.md"
        contents = grid_document.read_text(encoding="utf-8")

        required_terms = [
            "`AxialGrid`",
            "`x_nodes`",
            "`dx_values`",
            "`node_count`",
            "`cell_count`",
            "positive axial direction",
            "uniform or non-uniform",
        ]
        missing_terms = [term for term in required_terms if term not in contents]

        self.assertEqual(
            [],
            missing_terms,
            msg=f"Missing required axial grid model terms: {missing_terms}",
        )


if __name__ == "__main__":
    unittest.main()
