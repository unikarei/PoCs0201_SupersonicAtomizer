from pathlib import Path
import unittest


class ThermoContractTestsDocumentTest(unittest.TestCase):
    def test_thermo_contract_tests_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        document = repository_root / "docs" / "thermo-contract-tests.md"

        self.assertTrue(document.is_file(), msg="Thermo contract tests document is missing.")

    def test_required_contract_test_topics_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        document = repository_root / "docs" / "thermo-contract-tests.md"
        contents = document.read_text(encoding="utf-8")

        required_terms = [
            "interface conformance",
            "SI unit conformance",
            "supported-state success cases",
            "failure behavior conformance",
            "deterministic behavior",
            "alternate steam backends",
        ]
        missing_terms = [term for term in required_terms if term not in contents]

        self.assertEqual([], missing_terms, msg=f"Missing required thermo contract-test topics: {missing_terms}")


if __name__ == "__main__":
    unittest.main()
