from pathlib import Path
import unittest


class TabulatedAreaInterpolationTest(unittest.TestCase):
    def test_interpolation_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        interpolation_document = repository_root / "docs" / "tabulated-area-interpolation.md"

        self.assertTrue(
            interpolation_document.is_file(),
            msg="Tabulated area interpolation document is missing.",
        )

    def test_required_interpolation_topics_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        interpolation_document = repository_root / "docs" / "tabulated-area-interpolation.md"
        contents = interpolation_document.read_text(encoding="utf-8")

        required_terms = [
            "piecewise linear interpolation",
            "outside the supported domain",
            "strictly increasing",
            "duplicate `x` values are invalid",
            "nonpositive area values",
            "must not silently extrapolate",
        ]
        missing_terms = [term for term in required_terms if term not in contents]

        self.assertEqual(
            [],
            missing_terms,
            msg=f"Missing required interpolation topics: {missing_terms}",
        )


if __name__ == "__main__":
    unittest.main()
