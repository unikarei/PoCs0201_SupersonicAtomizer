from pathlib import Path
import unittest


class ProjectSkeletonTest(unittest.TestCase):
    def test_required_top_level_directories_exist(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        required_directories = [
            repository_root / "docs",
            repository_root / "src",
            repository_root / "tests",
            repository_root / "examples",
            repository_root / "outputs",
        ]

        missing_directories = [
            str(directory) for directory in required_directories if not directory.is_dir()
        ]

        self.assertEqual(
            [],
            missing_directories,
            msg=f"Missing required project directories: {missing_directories}",
        )


if __name__ == "__main__":
    unittest.main()
