from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.common import ConfigurationError
from supersonic_atomizer.domain import BoundaryConditionConfig
from supersonic_atomizer.solvers.gas import (
    GasBoundaryConditionState,
    initialize_gas_boundary_conditions,
)
from supersonic_atomizer.thermo import AirThermoProvider


class TestRuntimeGasBoundaryConditions(unittest.TestCase):
    def test_initializes_supported_subsonic_boundary_state(self) -> None:
        boundary_conditions = BoundaryConditionConfig(
            Pt_in=150000.0,
            Tt_in=320.0,
            Ps_out=100000.0,
        )

        boundary_state = initialize_gas_boundary_conditions(
            boundary_conditions,
            AirThermoProvider(),
        )

        self.assertIsInstance(boundary_state, GasBoundaryConditionState)
        self.assertEqual(boundary_state.total_pressure, 150000.0)
        self.assertEqual(boundary_state.total_temperature, 320.0)
        self.assertAlmostEqual(boundary_state.outlet_pressure_ratio, 2.0 / 3.0)
        self.assertGreater(boundary_state.outlet_mach_number, 0.0)
        self.assertLess(boundary_state.outlet_mach_number, 1.0)

    def test_rejects_invalid_boundary_combination_for_supported_closure(self) -> None:
        boundary_conditions = BoundaryConditionConfig(
            Pt_in=100000.0,
            Tt_in=320.0,
            Ps_out=100000.0,
        )

        with self.assertRaises(ConfigurationError):
            initialize_gas_boundary_conditions(boundary_conditions, AirThermoProvider())

    def test_clamps_choked_outlet_conditions_to_sonic_boundary_state(self) -> None:
        boundary_conditions = BoundaryConditionConfig(
            Pt_in=500000.0,
            Tt_in=320.0,
            Ps_out=100000.0,
        )

        boundary_state = initialize_gas_boundary_conditions(boundary_conditions, AirThermoProvider())

        self.assertEqual(boundary_state.outlet_mach_number, 1.0)


if __name__ == "__main__":
    unittest.main()