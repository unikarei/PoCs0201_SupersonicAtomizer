from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.domain import (
    BoundaryConditionConfig,
    CaseConfig,
    DropletInjectionConfig,
    FluidConfig,
    GeometryConfig,
    ModelSelectionConfig,
    OutputConfig,
)


class TestRuntimeCaseConfigurationModels(unittest.TestCase):
    def test_constructs_all_case_configuration_models(self) -> None:
        fluid = FluidConfig(working_fluid="air")
        boundary_conditions = BoundaryConditionConfig(
            Pt_in=600000.0,
            Tt_in=500.0,
            Ps_out=100000.0,
        )
        geometry = GeometryConfig(
            x_start=0.0,
            x_end=0.1,
            n_cells=10,
            area_definition={
                "type": "table",
                "x": [0.0, 0.1],
                "A": [1.0e-4, 1.2e-4],
            },
        )
        droplet_injection = DropletInjectionConfig(
            droplet_velocity_in=10.0,
            droplet_diameter_mean_in=1.0e-4,
            droplet_diameter_max_in=3.0e-4,
        )
        models = ModelSelectionConfig()
        outputs = OutputConfig()

        case_config = CaseConfig(
            case_name="air_baseline",
            case_description="Baseline air case",
            config_version=1,
            fluid=fluid,
            boundary_conditions=boundary_conditions,
            geometry=geometry,
            droplet_injection=droplet_injection,
            models=models,
            outputs=outputs,
        )

        self.assertEqual(case_config.case_name, "air_baseline")
        self.assertEqual(case_config.fluid.working_fluid, "air")
        self.assertEqual(case_config.boundary_conditions.Pt_in, 600000.0)
        self.assertEqual(case_config.geometry.n_cells, 10)
        self.assertEqual(case_config.droplet_injection.droplet_velocity_in, 10.0)
        self.assertEqual(case_config.models.drag_model, "standard_sphere")
        self.assertTrue(case_config.outputs.write_csv)

    def test_optional_fields_remain_optional(self) -> None:
        fluid = FluidConfig(working_fluid="steam", inlet_wetness=None)
        droplet_injection = DropletInjectionConfig(
            droplet_velocity_in=12.0,
            droplet_diameter_mean_in=1.5e-4,
            droplet_diameter_max_in=2.5e-4,
            water_mass_flow_rate=None,
        )
        models = ModelSelectionConfig(
            breakup_factor_mean=None,
            breakup_factor_max=None,
            steam_property_model=None,
        )

        self.assertIsNone(fluid.inlet_wetness)
        self.assertIsNone(droplet_injection.water_mass_flow_rate)
        self.assertIsNone(models.breakup_factor_mean)
        self.assertIsNone(models.breakup_factor_max)
        self.assertIsNone(models.steam_property_model)

    def test_geometry_preserves_area_definition_mapping(self) -> None:
        area_definition = {
            "type": "table",
            "x": [0.0, 0.05, 0.1],
            "A": [1.0e-4, 0.9e-4, 1.1e-4],
        }

        geometry = GeometryConfig(
            x_start=0.0,
            x_end=0.1,
            n_cells=20,
            area_definition=area_definition,
        )

        self.assertIs(geometry.area_definition, area_definition)
        self.assertEqual(geometry.area_definition["type"], "table")


if __name__ == "__main__":
    unittest.main()