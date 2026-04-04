from pathlib import Path
import unittest


class DefaultsPolicyTest(unittest.TestCase):
    def test_defaults_policy_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        policy_document = repository_root / "docs" / "defaults-policy.md"

        self.assertTrue(
            policy_document.is_file(),
            msg="Defaults policy document is missing.",
        )

    def test_required_default_decisions_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        policy_document = repository_root / "docs" / "defaults-policy.md"
        contents = policy_document.read_text(encoding="utf-8")

        required_terms = [
            "`weber_critical`",
            "`standard_sphere`",
            "`outputs.generate_plots`",
            "`fluid.inlet_wetness`",
            "`outputs.output_directory`",
            "must not be silently defaulted",
        ]
        missing_terms = [term for term in required_terms if term not in contents]

        self.assertEqual(
            [],
            missing_terms,
            msg=f"Missing required defaults policy terms: {missing_terms}",
        )


if __name__ == "__main__":
    unittest.main()
