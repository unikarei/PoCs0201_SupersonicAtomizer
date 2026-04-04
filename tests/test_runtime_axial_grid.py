from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.common import ConfigurationError
from supersonic_atomizer.domain import GeometryConfig
from supersonic_atomizer.grid import AxialGrid, build_axial_grid


class TestRuntimeAxialGrid(unittest.TestCase):
    def test_builds_uniform_axial_grid_from_geometry_config(self) -> None:
        geometry = GeometryConfig(
            x_start=0.0,
            x_end=0.1,
            n_cells=10,
            area_definition={
                "type": "table",
                "x": [0.0, 0.1],
                "A": [1.0e-4, 1.1e-4],
            },
        )

        grid = build_axial_grid(geometry)

        self.assertIsInstance(grid, AxialGrid)
        self.assertEqual(grid.x_nodes[0], 0.0)
        self.assertEqual(grid.x_nodes[-1], 0.1)
        self.assertEqual(grid.node_count, 11)
        self.assertEqual(grid.cell_count, 10)
        self.assertTrue(grid.is_uniform)
        self.assertAlmostEqual(grid.nominal_dx, 0.01)
        self.assertAlmostEqual(grid.domain_length, 0.1)
        self.assertEqual(len(grid.dx_values), 10)
        for dx in grid.dx_values:
            self.assertAlmostEqual(dx, 0.01)

    def test_grid_nodes_are_strictly_increasing(self) -> None:
        geometry = GeometryConfig(
            x_start=0.2,
            x_end=0.5,
            n_cells=3,
            area_definition={
                "type": "table",
                "x": [0.2, 0.5],
                "A": [1.0e-4, 1.2e-4],
            },
        )

        grid = build_axial_grid(geometry)

        self.assertEqual(grid.x_nodes, (0.2, 0.3, 0.4, 0.5))
        self.assertTrue(
            all(left < right for left, right in zip(grid.x_nodes, grid.x_nodes[1:]))
        )

    def test_rejects_invalid_grid_extent(self) -> None:
        geometry = GeometryConfig(
            x_start=0.1,
            x_end=0.1,
            n_cells=10,
            area_definition={
                "type": "table",
                "x": [0.1, 0.1],
                "A": [1.0e-4, 1.0e-4],
            },
        )

        with self.assertRaises(ConfigurationError):
            build_axial_grid(geometry)

    def test_rejects_nonpositive_or_noninteger_cell_counts(self) -> None:
        zero_cell_geometry = GeometryConfig(
            x_start=0.0,
            x_end=0.1,
            n_cells=0,
            area_definition={
                "type": "table",
                "x": [0.0, 0.1],
                "A": [1.0e-4, 1.2e-4],
            },
        )
        noninteger_cell_geometry = GeometryConfig(
            x_start=0.0,
            x_end=0.1,
            n_cells=3.5,
            area_definition={
                "type": "table",
                "x": [0.0, 0.1],
                "A": [1.0e-4, 1.2e-4],
            },
        )

        with self.assertRaises(ConfigurationError):
            build_axial_grid(zero_cell_geometry)

        with self.assertRaises(ConfigurationError):
            build_axial_grid(noninteger_cell_geometry)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()