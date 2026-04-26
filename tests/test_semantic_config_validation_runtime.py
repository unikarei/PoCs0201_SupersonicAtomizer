from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.config.defaults import apply_config_defaults
from supersonic_atomizer.config.semantics import validate_semantic_config


def _make_valid_config() -> dict:
    return apply_config_defaults(
        {
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
    )


class TestSemanticConfigValidationRuntime(unittest.TestCase):
    def test_accepts_valid_semantic_config(self) -> None:
        raw_config = _make_valid_config()

        validated = validate_semantic_config(raw_config)

        self.assertIs(validated, raw_config)

    def test_rejects_unsupported_working_fluid(self) -> None:
        raw_config = _make_valid_config()
        raw_config["fluid"]["working_fluid"] = "nitrogen"

        with self.assertRaises(ValueError):
            validate_semantic_config(raw_config)

    def test_rejects_nonpositive_boundary_condition(self) -> None:
        raw_config = _make_valid_config()
        raw_config["boundary_conditions"]["Ps_out"] = 0.0

        with self.assertRaises(ValueError):
            validate_semantic_config(raw_config)

    def test_rejects_invalid_grid_extent(self) -> None:
        raw_config = _make_valid_config()
        raw_config["geometry"]["x_end"] = raw_config["geometry"]["x_start"]

        with self.assertRaises(ValueError):
            validate_semantic_config(raw_config)

    def test_rejects_invalid_area_table_lengths(self) -> None:
        raw_config = _make_valid_config()
        raw_config["geometry"]["area_distribution"]["A"] = [1.0e-4]

        with self.assertRaises(ValueError):
            validate_semantic_config(raw_config)

    def test_rejects_non_increasing_area_coordinates(self) -> None:
        raw_config = _make_valid_config()
        raw_config["geometry"]["area_distribution"]["x"] = [0.0, 0.0]

        with self.assertRaises(ValueError):
            validate_semantic_config(raw_config)

    def test_rejects_air_case_with_wetness_set(self) -> None:
        raw_config = _make_valid_config()
        raw_config["fluid"]["inlet_wetness"] = 0.1

        with self.assertRaises(ValueError):
            validate_semantic_config(raw_config)

    def test_rejects_max_diameter_smaller_than_mean(self) -> None:
        raw_config = _make_valid_config()
        raw_config["droplet_injection"]["droplet_diameter_max_in"] = 5.0e-5

        with self.assertRaises(ValueError):
            validate_semantic_config(raw_config)

    def test_rejects_nonpositive_critical_weber_number(self) -> None:
        raw_config = _make_valid_config()
        raw_config["models"]["critical_weber_number"] = -1.0

        with self.assertRaises(ValueError):
            validate_semantic_config(raw_config)

    def test_accepts_two_way_approx_with_water_mass_flow_rate(self) -> None:
        raw_config = _make_valid_config()
        raw_config["models"]["coupling_mode"] = "two_way_approx"
        raw_config["droplet_injection"]["water_mass_flow_rate"] = 0.05

        validated = validate_semantic_config(raw_config)

        self.assertIs(validated, raw_config)

    def test_rejects_two_way_approx_without_water_mass_flow_rate(self) -> None:
        raw_config = _make_valid_config()
        raw_config["models"]["coupling_mode"] = "two_way_approx"

        with self.assertRaises(ValueError):
            validate_semantic_config(raw_config)

    def test_accepts_two_way_coupled_with_water_mass_flow_rate(self) -> None:
        raw_config = _make_valid_config()
        raw_config["models"]["coupling_mode"] = "two_way_coupled"
        raw_config["droplet_injection"]["water_mass_flow_rate"] = 0.05

        validated = validate_semantic_config(raw_config)

        self.assertIs(validated, raw_config)

    def test_rejects_two_way_coupled_without_water_mass_flow_rate(self) -> None:
        raw_config = _make_valid_config()
        raw_config["models"]["coupling_mode"] = "two_way_coupled"

        with self.assertRaises(ValueError):
            validate_semantic_config(raw_config)

    def test_rejects_invalid_distribution_model(self) -> None:
        raw_config = _make_valid_config()
        raw_config["models"]["droplet_distribution_model"] = "bimodal"

        with self.assertRaises(ValueError):
            validate_semantic_config(raw_config)

    def test_rejects_unknown_coupling_mode(self) -> None:
        raw_config = _make_valid_config()
        raw_config["models"]["coupling_mode"] = "two_way_exact"

        with self.assertRaises(ValueError):
            validate_semantic_config(raw_config)


if __name__ == "__main__":
    unittest.main()