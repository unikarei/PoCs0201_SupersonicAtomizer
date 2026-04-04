from pathlib import Path
import unittest


class ThermoBackendSelectionTest(unittest.TestCase):
    def test_backend_selection_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        document = repository_root / "docs" / "thermo-backend-selection.md"

        self.assertTrue(document.is_file(), msg="Thermo backend selection document is missing.")

    def test_required_backend_selection_topics_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        document = repository_root / "docs" / "thermo-backend-selection.md"
        contents = document.read_text(encoding="utf-8")

        required_terms = [
            "`fluid.working_fluid`",
            "`models.steam_property_model`",
            "unsupported",
            "air",
            "steam",
            "configuration-driven",
        ]
        missing_terms = [term for term in required_terms if term not in contents]

        self.assertEqual([], missing_terms, msg=f"Missing required backend selection topics: {missing_terms}")


if __name__ == "__main__":
    unittest.main()
