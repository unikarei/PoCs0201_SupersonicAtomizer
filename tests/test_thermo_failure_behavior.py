from pathlib import Path
import unittest


class ThermoFailureBehaviorTest(unittest.TestCase):
    def test_thermo_failure_behavior_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        document = repository_root / "docs" / "thermo-failure-behavior.md"

        self.assertTrue(document.is_file(), msg="Thermo failure behavior document is missing.")

    def test_required_failure_topics_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        document = repository_root / "docs" / "thermo-failure-behavior.md"
        contents = document.read_text(encoding="utf-8")

        required_terms = [
            "invalid state requests",
            "backend absence",
            "out-of-range",
            "unsupported phase-region",
            "must not swallow thermo failures",
            "error taxonomy",
        ]
        missing_terms = [term for term in required_terms if term not in contents]

        self.assertEqual([], missing_terms, msg=f"Missing required thermo failure topics: {missing_terms}")


if __name__ == "__main__":
    unittest.main()
