from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.config.schema import validate_raw_config_schema


class TestRawConfigSchemaValidation(unittest.TestCase):
    def test_accepts_valid_minimal_raw_config(self) -> None:
        raw_config = {
            "fluid": {"working_fluid": "air"},
            "boundary_conditions": {
                "Pt_in": 600000.0,
                "Tt_in": 500.0,
                "Ps_out": 100000.0,
            },
            "geometry": {
                "x_start": 0.0,
                "x_end": 0.1,
                "n_cells": 10,
                "area_distribution": {
                    "type": "table",
                    "x": [0.0, 0.1],
                    "A": [1.0e-4, 1.2e-4],
                },
            },
            "droplet_injection": {
                "droplet_velocity_in": 10.0,
                "droplet_diameter_mean_in": 1.0e-4,
                "droplet_diameter_max_in": 3.0e-4,
            },
        }

        validated = validate_raw_config_schema(raw_config)

        self.assertIs(validated, raw_config)

    def test_rejects_missing_required_section(self) -> None:
        raw_config = {
            "boundary_conditions": {
                "Pt_in": 600000.0,
                "Tt_in": 500.0,
                "Ps_out": 100000.0,
            },
            "geometry": {
                "x_start": 0.0,
                "x_end": 0.1,
                "n_cells": 10,
                "area_distribution": {
                    "type": "table",
                    "x": [0.0, 0.1],
                    "A": [1.0e-4, 1.2e-4],
                },
            },
            "droplet_injection": {
                "droplet_velocity_in": 10.0,
                "droplet_diameter_mean_in": 1.0e-4,
                "droplet_diameter_max_in": 3.0e-4,
            },
        }

        with self.assertRaises(ValueError):
            validate_raw_config_schema(raw_config)

    def test_rejects_missing_required_field(self) -> None:
        raw_config = {
            "fluid": {"working_fluid": "air"},
            "boundary_conditions": {
                "Pt_in": 600000.0,
                "Tt_in": 500.0,
            },
            "geometry": {
                "x_start": 0.0,
                "x_end": 0.1,
                "n_cells": 10,
                "area_distribution": {
                    "type": "table",
                    "x": [0.0, 0.1],
                    "A": [1.0e-4, 1.2e-4],
                },
            },
            "droplet_injection": {
                "droplet_velocity_in": 10.0,
                "droplet_diameter_mean_in": 1.0e-4,
                "droplet_diameter_max_in": 3.0e-4,
            },
        }

        with self.assertRaises(ValueError):
            validate_raw_config_schema(raw_config)

    def test_rejects_invalid_nested_shape(self) -> None:
        raw_config = {
            "fluid": {"working_fluid": "air"},
            "boundary_conditions": {
                "Pt_in": 600000.0,
                "Tt_in": 500.0,
                "Ps_out": 100000.0,
            },
            "geometry": {
                "x_start": 0.0,
                "x_end": 0.1,
                "n_cells": 10,
                "area_distribution": {
                    "type": "table",
                    "x": "0.0,0.1",
                    "A": [1.0e-4, 1.2e-4],
                },
            },
            "droplet_injection": {
                "droplet_velocity_in": 10.0,
                "droplet_diameter_mean_in": 1.0e-4,
                "droplet_diameter_max_in": 3.0e-4,
            },
        }

        with self.assertRaises(ValueError):
            validate_raw_config_schema(raw_config)

    def test_rejects_invalid_area_distribution_type(self) -> None:
        raw_config = {
            "fluid": {"working_fluid": "air"},
            "boundary_conditions": {
                "Pt_in": 600000.0,
                "Tt_in": 500.0,
                "Ps_out": 100000.0,
            },
            "geometry": {
                "x_start": 0.0,
                "x_end": 0.1,
                "n_cells": 10,
                "area_distribution": {
                    "type": "analytic",
                    "x": [0.0, 0.1],
                    "A": [1.0e-4, 1.2e-4],
                },
            },
            "droplet_injection": {
                "droplet_velocity_in": 10.0,
                "droplet_diameter_mean_in": 1.0e-4,
                "droplet_diameter_max_in": 3.0e-4,
            },
        }

        with self.assertRaises(ValueError):
            validate_raw_config_schema(raw_config)


if __name__ == "__main__":
    unittest.main()