from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.common import ConfigurationError
from supersonic_atomizer.domain import GeometryConfig
from supersonic_atomizer.geometry import (
    TabulatedAreaProfile,
    build_tabulated_area_profile,
)


class TestRuntimeTabulatedAreaProfile(unittest.TestCase):
    def test_builds_tabulated_area_profile_from_geometry_config(self) -> None:
        geometry = GeometryConfig(
            x_start=0.0,
            x_end=0.2,
            n_cells=20,
            area_definition={
                "type": "table",
                "x": [0.0, 0.1, 0.2],
                "A": [1.0e-4, 0.9e-4, 1.1e-4],
            },
        )

        profile = build_tabulated_area_profile(geometry)

        self.assertIsInstance(profile, TabulatedAreaProfile)
        self.assertEqual(profile.x_points, (0.0, 0.1, 0.2))
        self.assertEqual(profile.area_values, (1.0e-4, 0.9e-4, 1.1e-4))
        self.assertEqual(profile.profile_type, "table")
        self.assertTrue(profile.is_tabulated)
        self.assertEqual(profile.x_min, 0.0)
        self.assertEqual(profile.x_max, 0.2)
        self.assertEqual(
            profile.source_points,
            ((0.0, 1.0e-4), (0.1, 0.9e-4), (0.2, 1.1e-4)),
        )

    def test_supports_queries_within_profile_domain(self) -> None:
        profile = TabulatedAreaProfile(
            x_points=(0.0, 0.05, 0.1),
            area_values=(1.0e-4, 1.1e-4, 1.2e-4),
        )

        self.assertTrue(profile.supports(0.0))
        self.assertTrue(profile.supports(0.075))
        self.assertTrue(profile.supports(0.1))
        self.assertFalse(profile.supports(-0.001))
        self.assertFalse(profile.supports(0.101))

    def test_area_at_returns_exact_tabulated_values_at_nodes(self) -> None:
        profile = TabulatedAreaProfile(
            x_points=(0.0, 0.1, 0.2),
            area_values=(1.0e-4, 0.8e-4, 1.2e-4),
        )

        self.assertEqual(profile.area_at(0.0), 1.0e-4)
        self.assertEqual(profile.area_at(0.1), 0.8e-4)
        self.assertEqual(profile.area_at(0.2), 1.2e-4)

    def test_area_at_linearly_interpolates_between_bracketing_points(self) -> None:
        profile = TabulatedAreaProfile(
            x_points=(0.0, 0.1, 0.2),
            area_values=(1.0e-4, 0.8e-4, 1.2e-4),
        )

        self.assertAlmostEqual(profile.area_at(0.05), 0.9e-4)
        self.assertAlmostEqual(profile.area_at(0.15), 1.0e-4)

    def test_area_at_rejects_out_of_range_queries(self) -> None:
        profile = TabulatedAreaProfile(
            x_points=(0.0, 0.1),
            area_values=(1.0e-4, 1.2e-4),
        )

        with self.assertRaises(ConfigurationError):
            profile.area_at(-1.0e-6)

        with self.assertRaises(ConfigurationError):
            profile.area_at(0.100001)

    def test_rejects_nonpositive_area_values(self) -> None:
        with self.assertRaises(ConfigurationError):
            TabulatedAreaProfile(
                x_points=(0.0, 0.1),
                area_values=(1.0e-4, 0.0),
            )


if __name__ == "__main__":
    unittest.main()