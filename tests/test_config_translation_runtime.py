from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.config.defaults import apply_config_defaults
from supersonic_atomizer.config.translator import translate_case_config
from supersonic_atomizer.domain import CaseConfig


class TestConfigTranslationRuntime(unittest.TestCase):
    def test_translates_representative_air_case(self) -> None:
        normalized = apply_config_defaults(
            {
                "case": {
                    "name": "air_baseline",
                    "description": "Baseline air case",
                    "config_version": 1,
                },
                "fluid": {"working_fluid": "air"},
                "boundary_conditions": {
                    "Pt_in": 600000.0,
                    "Tt_in": 500.0,
                    "Ps_out": 100000.0,
                },
                "geometry": {
                    "x_start": 0.0,
                    "x_end": 0.1,
                    "n_cells": 20,
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

        case_config = translate_case_config(normalized)

        self.assertIsInstance(case_config, CaseConfig)
        self.assertEqual(case_config.case_name, "air_baseline")
        self.assertEqual(case_config.fluid.working_fluid, "air")
        self.assertEqual(case_config.boundary_conditions.Ps_out, 100000.0)
        self.assertEqual(case_config.geometry.area_definition["type"], "table")
        self.assertEqual(case_config.models.drag_model, "standard_sphere")
        self.assertEqual(case_config.models.droplet_distribution_model, "mono")
        self.assertEqual(case_config.models.two_way_convergence_tolerance, 1.0e-3)
        self.assertEqual(case_config.outputs.output_directory, "outputs")

    def test_translates_representative_steam_case_with_explicit_options(self) -> None:
        normalized = apply_config_defaults(
            {
                "fluid": {
                    "working_fluid": "steam",
                    "inlet_wetness": 0.03,
                },
                "boundary_conditions": {
                    "Pt_in": 700000.0,
                    "Tt_in": 520.0,
                    "Ps_out": 120000.0,
                },
                "geometry": {
                    "x_start": 0.0,
                    "x_end": 0.2,
                    "n_cells": 40,
                    "area_distribution": {
                        "type": "table",
                        "x": [0.0, 0.1, 0.2],
                        "A": [1.2e-4, 0.9e-4, 1.1e-4],
                    },
                },
                "droplet_injection": {
                    "droplet_velocity_in": 15.0,
                    "droplet_diameter_mean_in": 1.2e-4,
                    "droplet_diameter_max_in": 2.4e-4,
                    "water_mass_flow_rate": 0.001,
                    "water_mass_flow_rate_percent": 4.5,
                },
                "models": {
                    "drag_model": "standard_sphere",
                    "breakup_model": "weber_critical",
                    "coupling_mode": "two_way_approx",
                    "two_way_max_iterations": 4,
                    "two_way_feedback_relaxation": 0.2,
                    "two_way_convergence_tolerance": 5.0e-4,
                    "droplet_distribution_model": "lognormal_moments",
                    "droplet_distribution_sigma": 0.45,
                    "critical_weber_number": 15.0,
                    "breakup_factor_mean": 0.7,
                    "breakup_factor_max": 0.6,
                    "steam_property_model": "if97",
                },
                "outputs": {
                    "output_directory": "custom_outputs",
                    "write_csv": True,
                    "write_json": False,
                    "generate_plots": False,
                },
            }
        )

        case_config = translate_case_config(normalized)

        self.assertEqual(case_config.fluid.working_fluid, "steam")
        self.assertEqual(case_config.fluid.inlet_wetness, 0.03)
        self.assertEqual(case_config.droplet_injection.water_mass_flow_rate, 0.001)
        self.assertEqual(case_config.droplet_injection.water_mass_flow_rate_percent, 4.5)
        self.assertEqual(case_config.models.coupling_mode, "two_way_approx")
        self.assertEqual(case_config.models.two_way_max_iterations, 4)
        self.assertEqual(case_config.models.two_way_feedback_relaxation, 0.2)
        self.assertEqual(case_config.models.two_way_convergence_tolerance, 5.0e-4)
        self.assertEqual(case_config.models.droplet_distribution_model, "lognormal_moments")
        self.assertEqual(case_config.models.droplet_distribution_sigma, 0.45)
        self.assertEqual(case_config.models.critical_weber_number, 15.0)
        self.assertEqual(case_config.models.steam_property_model, "if97")
        self.assertEqual(case_config.outputs.output_directory, "custom_outputs")
        self.assertFalse(case_config.outputs.write_json)
        self.assertFalse(case_config.outputs.generate_plots)


if __name__ == "__main__":
    unittest.main()