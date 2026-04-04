from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.common import ConfigurationError
from supersonic_atomizer.domain import GeometryConfig
from supersonic_atomizer.geometry import GeometryModel, build_geometry_model
from supersonic_atomizer.geometry.area_profile import TabulatedAreaProfile
from supersonic_atomizer.grid import AxialGrid


class TestRuntimeGeometryModel(unittest.TestCase):
    def test_builds_geometry_model_with_aligned_grid_and_area_profile(self) -> None:
        geometry_config = GeometryConfig(
            x_start=0.0,
            x_end=0.2,
            n_cells=4,
            area_definition={
                "type": "table",
                "x": [0.0, 0.1, 0.2],
                "A": [1.0e-4, 0.8e-4, 1.2e-4],
            },
        )

        geometry_model = build_geometry_model(geometry_config)

        self.assertIsInstance(geometry_model, GeometryModel)
        self.assertEqual(geometry_model.x_start, 0.0)
        self.assertEqual(geometry_model.x_end, 0.2)
        self.assertAlmostEqual(geometry_model.length, 0.2)
        self.assertEqual(geometry_model.area_profile_type, "table")
        self.assertTrue(geometry_model.is_tabulated_profile)
        self.assertEqual(geometry_model.grid.x_nodes, (0.0, 0.05, 0.1, 0.15000000000000002, 0.2))
        self.assertEqual(
            geometry_model.area_profile_data,
            ((0.0, 1.0e-4), (0.1, 0.8e-4), (0.2, 1.2e-4)),
        )
        self.assertTrue(geometry_model.supports(0.1))
        self.assertAlmostEqual(geometry_model.area_at(0.05), 0.9e-4)

    def test_rejects_misaligned_grid_domain(self) -> None:
        aligned_profile = TabulatedAreaProfile(
            x_points=(0.0, 0.1),
            area_values=(1.0e-4, 1.2e-4),
        )
        misaligned_grid = AxialGrid(
            x_nodes=(0.05, 0.1, 0.15),
            dx_values=(0.05, 0.05),
            x_start=0.05,
            x_end=0.15,
            nominal_dx=0.05,
            is_uniform=True,
            node_count=3,
            cell_count=2,
            domain_length=0.1,
        )

        with self.assertRaises(ConfigurationError):
            GeometryModel(
                x_start=0.0,
                x_end=0.1,
                length=0.1,
                area_profile_type="table",
                area_profile_data=aligned_profile.source_points,
                is_tabulated_profile=True,
                grid=misaligned_grid,
                area_profile=aligned_profile,
            )

    def test_rejects_misaligned_area_profile_domain(self) -> None:
        aligned_grid = AxialGrid(
            x_nodes=(0.0, 0.05, 0.1),
            dx_values=(0.05, 0.05),
            x_start=0.0,
            x_end=0.1,
            nominal_dx=0.05,
            is_uniform=True,
            node_count=3,
            cell_count=2,
            domain_length=0.1,
        )
        misaligned_profile = TabulatedAreaProfile(
            x_points=(0.02, 0.1),
            area_values=(1.0e-4, 1.2e-4),
        )

        with self.assertRaises(ConfigurationError):
            GeometryModel(
                x_start=0.0,
                x_end=0.1,
                length=0.1,
                area_profile_type="table",
                area_profile_data=misaligned_profile.source_points,
                is_tabulated_profile=True,
                grid=aligned_grid,
                area_profile=misaligned_profile,
            )


if __name__ == "__main__":
    unittest.main()