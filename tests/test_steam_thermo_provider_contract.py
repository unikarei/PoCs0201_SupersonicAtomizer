from pathlib import Path
import unittest


class SteamThermoProviderContractTest(unittest.TestCase):
    def test_steam_provider_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        document = repository_root / "docs" / "steam-thermo-provider-contract.md"

        self.assertTrue(document.is_file(), msg="Steam thermo provider contract document is missing.")

    def test_required_steam_contract_topics_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        document = repository_root / "docs" / "steam-thermo-provider-contract.md"
        contents = document.read_text(encoding="utf-8")

        required_terms = [
            "equilibrium steam",
            "IF97",
            "pressure",
            "temperature",
            "density",
            "phase-region",
        ]
        missing_terms = [term for term in required_terms if term not in contents]

        self.assertEqual([], missing_terms, msg=f"Missing required steam contract topics: {missing_terms}")


if __name__ == "__main__":
    unittest.main()
