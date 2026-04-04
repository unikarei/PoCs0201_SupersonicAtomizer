from pathlib import Path
import unittest


class ThermoProviderInterfaceTest(unittest.TestCase):
    def test_thermo_provider_interface_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        document = repository_root / "docs" / "thermo-provider-interface.md"

        self.assertTrue(document.is_file(), msg="Thermo provider interface document is missing.")

    def test_required_interface_topics_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        document = repository_root / "docs" / "thermo-provider-interface.md"
        contents = document.read_text(encoding="utf-8")

        required_terms = [
            "`ThermoProvider`",
            "density",
            "sound speed",
            "enthalpy",
            "metadata",
            "error conditions",
        ]
        missing_terms = [term for term in required_terms if term not in contents]

        self.assertEqual([], missing_terms, msg=f"Missing required thermo interface topics: {missing_terms}")


if __name__ == "__main__":
    unittest.main()
