from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.common import ConfigurationError
from supersonic_atomizer.domain import GeometryConfig
from supersonic_atomizer.geometry import (
    build_geometry_model,
    validate_geometry_config_diagnostics,
)


class TestRuntimeGeometryGridDiagnostics(unittest.TestCase):
    def test_rejects_invalid_axial_range(self) -> None:
        geometry_config = GeometryConfig(
            x_start=0.2,
            x_end=0.1,
            n_cells=5,
            area_definition={
                "type": "table",
                "x": [0.2, 0.1],
                "A": [1.0e-4, 1.1e-4],
            },
        )

        with self.assertRaises(ConfigurationError):
            validate_geometry_config_diagnostics(geometry_config)

    def test_rejects_inconsistent_area_table_lengths(self) -> None:
        geometry_config = GeometryConfig(
            x_start=0.0,
            x_end=0.2,
            n_cells=4,
            area_definition={
                "type": "table",
                "x": [0.0, 0.1, 0.2],
                "A": [1.0e-4, 1.1e-4],
            },
        )

        with self.assertRaises(ConfigurationError):
            validate_geometry_config_diagnostics(geometry_config)

    def test_rejects_degenerate_grid_conditions(self) -> None:
        geometry_config = GeometryConfig(
            x_start=0.0,
            x_end=0.2,
            n_cells=0,
            area_definition={
                "type": "table",
                "x": [0.0, 0.2],
                "A": [1.0e-4, 1.1e-4],
            },
        )

        with self.assertRaises(ConfigurationError):
            validate_geometry_config_diagnostics(geometry_config)

    def test_build_geometry_model_uses_runtime_diagnostics(self) -> None:
        geometry_config = GeometryConfig(
            x_start=0.0,
            x_end=0.2,
            n_cells=4,
            area_definition={
                "type": "table",
                "x": [0.0, 0.1, 0.2],
                "A": [1.0e-4, 0.9e-4, 1.2e-4],
            },
        )

        geometry_model = build_geometry_model(geometry_config)

        self.assertAlmostEqual(geometry_model.length, 0.2)
        self.assertEqual(geometry_model.grid.node_count, 5)
        self.assertTrue(geometry_model.supports(0.15))


if __name__ == "__main__":
    unittest.main()