from pathlib import Path
import unittest


class AxialGeometryRepresentationTest(unittest.TestCase):
    def test_axial_geometry_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        geometry_document = repository_root / "docs" / "axial-geometry-representation.md"

        self.assertTrue(
            geometry_document.is_file(),
            msg="Axial geometry representation document is missing.",
        )

    def test_required_geometry_concepts_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        geometry_document = repository_root / "docs" / "axial-geometry-representation.md"
        contents = geometry_document.read_text(encoding="utf-8")

        required_terms = [
            "`GeometryModel`",
            "`x_start`",
            "`x_end`",
            "`length`",
            "`area_profile_type`",
            "`area_profile_data`",
            "tabulated",
            "solver-independent",
        ]
        missing_terms = [term for term in required_terms if term not in contents]

        self.assertEqual(
            [],
            missing_terms,
            msg=f"Missing required geometry representation terms: {missing_terms}",
        )


if __name__ == "__main__":
    unittest.main()
