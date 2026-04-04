from pathlib import Path
import unittest


class PackageLayoutTest(unittest.TestCase):
    def test_required_package_directories_exist(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        package_root = repository_root / "src" / "supersonic_atomizer"
        required_directories = [
            package_root,
            package_root / "app",
            package_root / "cli",
            package_root / "config",
            package_root / "domain",
            package_root / "thermo",
            package_root / "geometry",
            package_root / "grid",
            package_root / "solvers",
            package_root / "solvers" / "gas",
            package_root / "solvers" / "droplet",
            package_root / "breakup",
            package_root / "io",
            package_root / "plotting",
            package_root / "validation",
        ]

        missing_directories = [
            str(directory) for directory in required_directories if not directory.is_dir()
        ]

        self.assertEqual(
            [],
            missing_directories,
            msg=f"Missing required package directories: {missing_directories}",
        )

    def test_module_map_documents_package_name(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        module_map_path = repository_root / "docs" / "module-map.md"

        self.assertTrue(module_map_path.is_file(), msg="Module map document is missing.")
        self.assertIn(
            "`supersonic_atomizer`",
            module_map_path.read_text(encoding="utf-8"),
            msg="Package naming decision is not documented in the module map.",
        )


if __name__ == "__main__":
    unittest.main()
