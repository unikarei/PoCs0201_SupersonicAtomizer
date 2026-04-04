from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.common import (
    ConfigurationError,
    InputParsingError,
    ModelSelectionError,
    NumericalError,
    OutputError,
    SupersonicAtomizerError,
    ThermoError,
    ValidationError,
)


class TestRuntimeErrorClasses(unittest.TestCase):
    def test_error_classes_are_available_from_common_package(self) -> None:
        self.assertTrue(issubclass(InputParsingError, SupersonicAtomizerError))
        self.assertTrue(issubclass(ConfigurationError, SupersonicAtomizerError))
        self.assertTrue(issubclass(ModelSelectionError, SupersonicAtomizerError))
        self.assertTrue(issubclass(ThermoError, SupersonicAtomizerError))
        self.assertTrue(issubclass(NumericalError, SupersonicAtomizerError))
        self.assertTrue(issubclass(OutputError, SupersonicAtomizerError))
        self.assertTrue(issubclass(ValidationError, SupersonicAtomizerError))

    def test_error_instances_preserve_intended_categorization(self) -> None:
        errors = [
            InputParsingError("parse failure"),
            ConfigurationError("config failure"),
            ModelSelectionError("model failure"),
            ThermoError("thermo failure"),
            NumericalError("numerical failure"),
            OutputError("output failure"),
            ValidationError("validation failure"),
        ]

        for error in errors:
            self.assertIsInstance(error, SupersonicAtomizerError)
            self.assertIsInstance(error, Exception)

        self.assertEqual(str(errors[0]), "parse failure")
        self.assertEqual(str(errors[4]), "numerical failure")


if __name__ == "__main__":
    unittest.main()