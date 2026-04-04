from pathlib import Path
import unittest


class AreaProfileAbstractionTest(unittest.TestCase):
    def test_area_profile_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        abstraction_document = repository_root / "docs" / "area-profile-abstraction.md"

        self.assertTrue(
            abstraction_document.is_file(),
            msg="Area profile abstraction document is missing.",
        )

    def test_required_area_profile_concepts_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        abstraction_document = repository_root / "docs" / "area-profile-abstraction.md"
        contents = abstraction_document.read_text(encoding="utf-8")

        required_terms = [
            "`AreaProfile`",
            "`area_at(x)`",
            "`x_min`",
            "`x_max`",
            "`supports(x)`",
            "tabulated",
            "raw YAML",
            "gas solver",
        ]
        missing_terms = [term for term in required_terms if term not in contents]

        self.assertEqual(
            [],
            missing_terms,
            msg=f"Missing required area profile abstraction terms: {missing_terms}",
        )


if __name__ == "__main__":
    unittest.main()
