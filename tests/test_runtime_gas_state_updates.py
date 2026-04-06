from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.common import NumericalError
from supersonic_atomizer.domain import BoundaryConditionConfig, GasState
from supersonic_atomizer.solvers.gas import (
    assemble_gas_state,
    compute_area_mach_relation,
    compute_static_pressure,
    compute_static_temperature,
    initialize_gas_boundary_conditions,
    solve_subsonic_mach_from_area_ratio,
)
from supersonic_atomizer.thermo import AirThermoProvider


class TestRuntimeGasStateUpdates(unittest.TestCase):
    def test_area_mach_relation_and_inverse_are_consistent_for_supported_subsonic_state(self) -> None:
        heat_capacity_ratio = 1.4
        expected_mach_number = 0.35

        area_ratio = compute_area_mach_relation(expected_mach_number, heat_capacity_ratio)
        recovered_mach_number = solve_subsonic_mach_from_area_ratio(
            area_ratio,
            heat_capacity_ratio,
        )

        self.assertGreater(area_ratio, 1.0)
        self.assertAlmostEqual(recovered_mach_number, expected_mach_number, places=8)

    def test_static_pressure_and_temperature_remain_positive(self) -> None:
        static_pressure = compute_static_pressure(150000.0, 0.3, 1.4)
        static_temperature = compute_static_temperature(320.0, 0.3, 1.4)

        self.assertGreater(static_pressure, 0.0)
        self.assertGreater(static_temperature, 0.0)
        self.assertLess(static_pressure, 150000.0)
        self.assertLess(static_temperature, 320.0)

    def test_assembles_local_gas_state_from_boundary_state_and_mach_number(self) -> None:
        boundary_state = initialize_gas_boundary_conditions(
            BoundaryConditionConfig(Pt_in=150000.0, Tt_in=320.0, Ps_out=100000.0),
            AirThermoProvider(),
        )

        gas_state = assemble_gas_state(
            x_value=0.05,
            area_value=1.1e-4,
            mach_number=0.35,
            boundary_state=boundary_state,
            thermo_provider=AirThermoProvider(),
        )

        self.assertIsInstance(gas_state, GasState)
        self.assertEqual(gas_state.x, 0.05)
        self.assertEqual(gas_state.area, 1.1e-4)
        self.assertGreater(gas_state.pressure, 0.0)
        self.assertGreater(gas_state.temperature, 0.0)
        self.assertGreater(gas_state.density, 0.0)
        self.assertAlmostEqual(
            gas_state.mach_number,
            gas_state.velocity / gas_state.thermo_state.sound_speed,
            places=10,
        )

    def test_rejects_nonphysical_mach_in_gas_state_assembly(self) -> None:
        boundary_state = initialize_gas_boundary_conditions(
            BoundaryConditionConfig(Pt_in=150000.0, Tt_in=320.0, Ps_out=100000.0),
            AirThermoProvider(),
        )

        with self.assertRaises(NumericalError):
            assemble_gas_state(
                x_value=0.0,
                area_value=1.0e-4,
                mach_number=-0.1,
                boundary_state=boundary_state,
                thermo_provider=AirThermoProvider(),
            )


if __name__ == "__main__":
    unittest.main()