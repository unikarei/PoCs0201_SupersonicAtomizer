from pathlib import Path
import unittest


class GeometryGridDiagnosticsTest(unittest.TestCase):
    def test_geometry_grid_diagnostics_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        diagnostics_document = repository_root / "docs" / "geometry-grid-diagnostics.md"

        self.assertTrue(
            diagnostics_document.is_file(),
            msg="Geometry/grid diagnostics document is missing.",
        )

    def test_required_geometry_grid_diagnostic_topics_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        diagnostics_document = repository_root / "docs" / "geometry-grid-diagnostics.md"
        contents = diagnostics_document.read_text(encoding="utf-8")

        required_terms = [
            "invalid axial range",
            "nonpositive area",
            "inconsistent table length",
            "degenerate grid",
            "duplicate `x` values",
            "fatal pre-solver errors",
        ]
        missing_terms = [term for term in required_terms if term not in contents]

        self.assertEqual(
            [],
            missing_terms,
            msg=f"Missing required geometry/grid diagnostic topics: {missing_terms}",
        )


if __name__ == "__main__":
    unittest.main()
