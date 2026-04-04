from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.config.defaults import apply_config_defaults


class TestConfigDefaultsApplicationRuntime(unittest.TestCase):
    def test_applies_documented_mvp_defaults(self) -> None:
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
                "area_distribution": {"type": "table", "x": [0.0], "A": [1.0e-4]},
            },
            "droplet_injection": {
                "droplet_velocity_in": 10.0,
                "droplet_diameter_mean_in": 1.0e-4,
                "droplet_diameter_max_in": 3.0e-4,
            },
        }

        normalized = apply_config_defaults(raw_config)

        self.assertEqual(normalized["models"]["drag_model"], "standard_sphere")
        self.assertEqual(normalized["models"]["breakup_model"], "weber_critical")
        self.assertEqual(normalized["models"]["critical_weber_number"], 12.0)
        self.assertTrue(normalized["outputs"]["write_csv"])
        self.assertTrue(normalized["outputs"]["write_json"])
        self.assertTrue(normalized["outputs"]["generate_plots"])
        self.assertEqual(normalized["outputs"]["output_directory"], "outputs")
        self.assertIsNone(normalized["fluid"]["inlet_wetness"])

    def test_preserves_explicit_user_values(self) -> None:
        raw_config = {
            "fluid": {"working_fluid": "steam", "inlet_wetness": 0.05},
            "models": {
                "drag_model": "custom_drag",
                "breakup_model": "custom_breakup",
                "critical_weber_number": 18.5,
            },
            "outputs": {
                "write_csv": False,
                "write_json": False,
                "generate_plots": False,
                "output_directory": "custom_outputs",
            },
        }

        normalized = apply_config_defaults(raw_config)

        self.assertEqual(normalized["fluid"]["inlet_wetness"], 0.05)
        self.assertEqual(normalized["models"]["drag_model"], "custom_drag")
        self.assertEqual(normalized["models"]["breakup_model"], "custom_breakup")
        self.assertEqual(normalized["models"]["critical_weber_number"], 18.5)
        self.assertFalse(normalized["outputs"]["write_csv"])
        self.assertFalse(normalized["outputs"]["write_json"])
        self.assertFalse(normalized["outputs"]["generate_plots"])
        self.assertEqual(normalized["outputs"]["output_directory"], "custom_outputs")

    def test_leaves_non_defaulted_optional_fields_unset(self) -> None:
        raw_config = {
            "fluid": {"working_fluid": "air"},
            "models": {},
            "outputs": {},
        }

        normalized = apply_config_defaults(raw_config)

        self.assertNotIn("breakup_factor_mean", normalized["models"])
        self.assertNotIn("breakup_factor_max", normalized["models"])
        self.assertNotIn("steam_property_model", normalized["models"])
        self.assertNotIn("water_mass_flow_rate", normalized.get("droplet_injection", {}))
        self.assertNotIn("name", normalized.get("case", {}))

    def test_returns_new_mapping_without_mutating_input(self) -> None:
        raw_config = {"fluid": {"working_fluid": "air"}}

        normalized = apply_config_defaults(raw_config)

        self.assertIsNot(raw_config, normalized)
        self.assertNotIn("models", raw_config)
        self.assertIn("models", normalized)


if __name__ == "__main__":
    unittest.main()