from pathlib import Path
import unittest


class AirThermoProviderResponsibilitiesTest(unittest.TestCase):
    def test_air_provider_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        document = repository_root / "docs" / "air-thermo-provider-responsibilities.md"

        self.assertTrue(document.is_file(), msg="Air thermo provider document is missing.")

    def test_required_air_provider_topics_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        document = repository_root / "docs" / "air-thermo-provider-responsibilities.md"
        contents = document.read_text(encoding="utf-8")

        required_terms = [
            "ideal gas",
            "density",
            "sound speed",
            "enthalpy",
            "nonphysical",
            "thermo interface",
        ]
        missing_terms = [term for term in required_terms if term not in contents]

        self.assertEqual([], missing_terms, msg=f"Missing required air provider topics: {missing_terms}")


if __name__ == "__main__":
    unittest.main()
