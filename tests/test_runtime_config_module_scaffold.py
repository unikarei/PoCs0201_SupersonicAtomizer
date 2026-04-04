from pathlib import Path
import unittest


class TestRuntimeConfigModuleScaffold(unittest.TestCase):
    def test_required_config_modules_exist(self) -> None:
        config_dir = Path("src/supersonic_atomizer/config")

        for relative_path in [
            "__init__.py",
            "loader.py",
            "schema.py",
            "semantics.py",
            "defaults.py",
            "translator.py",
        ]:
            self.assertTrue((config_dir / relative_path).exists(), relative_path)

    def test_package_exports_expected_scaffold_entries(self) -> None:
        init_text = Path("src/supersonic_atomizer/config/__init__.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("load_raw_case_config", init_text)
        self.assertIn("validate_raw_config_schema", init_text)
        self.assertIn("validate_semantic_config", init_text)
        self.assertIn("apply_config_defaults", init_text)
        self.assertIn("translate_case_config", init_text)

    def test_scaffold_modules_preserve_config_boundaries(self) -> None:
        loader_text = Path("src/supersonic_atomizer/config/loader.py").read_text(
            encoding="utf-8"
        )
        schema_text = Path("src/supersonic_atomizer/config/schema.py").read_text(
            encoding="utf-8"
        )
        semantics_text = Path(
            "src/supersonic_atomizer/config/semantics.py"
        ).read_text(encoding="utf-8")
        translator_text = Path(
            "src/supersonic_atomizer/config/translator.py"
        ).read_text(encoding="utf-8")

        self.assertIn("must not perform schema validation", loader_text)
        self.assertIn("must not perform semantic validation", schema_text)
        self.assertIn("must remain separate from raw schema checks", semantics_text)
        self.assertIn("must not perform raw parsing or solver work", translator_text)


if __name__ == "__main__":
    unittest.main()