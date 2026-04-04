from pathlib import Path
import unittest


class YamlSchemaStructureTest(unittest.TestCase):
    def test_yaml_schema_document_exists(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        schema_document = repository_root / "docs" / "yaml-schema.md"

        self.assertTrue(
            schema_document.is_file(),
            msg="YAML schema structure document is missing.",
        )

    def test_required_sections_and_fields_are_documented(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        schema_document = repository_root / "docs" / "yaml-schema.md"
        contents = schema_document.read_text(encoding="utf-8")

        required_terms = [
            "`fluid`",
            "`boundary_conditions`",
            "`geometry`",
            "`droplet_injection`",
            "`models`",
            "`outputs`",
            "`working_fluid`",
            "`Pt_in`",
            "`Tt_in`",
            "`Ps_out`",
            "`area_distribution`",
            "`droplet_velocity_in`",
            "`droplet_diameter_mean_in`",
            "`droplet_diameter_max_in`",
        ]
        missing_terms = [term for term in required_terms if term not in contents]

        self.assertEqual(
            [],
            missing_terms,
            msg=f"Missing required YAML schema terms: {missing_terms}",
        )


if __name__ == "__main__":
    unittest.main()
