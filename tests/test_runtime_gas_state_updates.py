from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.common import NumericalError
from supersonic_atomizer.domain import BoundaryConditionConfig, GasState
from supersonic_atomizer.solvers.gas import (
    assemble_gas_state,
    assemble_gas_state_from_total_conditions,
    compute_area_mach_relation,
    compute_normal_shock_downstream_mach,
    compute_post_shock_total_pressure,
    compute_static_pressure,
    compute_static_temperature,
    compute_total_pressure,
    initialize_gas_boundary_conditions,
    solve_subsonic_mach_from_area_ratio,
    solve_supersonic_mach_from_area_ratio,
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

    def test_area_mach_relation_and_supersonic_inverse_are_consistent(self) -> None:
        area_ratio = compute_area_mach_relation(2.0, 1.4)
        recovered_mach_number = solve_supersonic_mach_from_area_ratio(area_ratio, 1.4)

        self.assertGreater(area_ratio, 1.0)
        self.assertAlmostEqual(recovered_mach_number, 2.0, places=8)

    def test_compute_total_pressure_recovers_stagnation_pressure(self) -> None:
        static_pressure = compute_static_pressure(200000.0, 0.8, 1.4)
        recovered_total_pressure = compute_total_pressure(static_pressure, 0.8, 1.4)

        self.assertAlmostEqual(recovered_total_pressure, 200000.0, places=6)

    def test_normal_shock_relations_reduce_mach_and_total_pressure(self) -> None:
        downstream_mach = compute_normal_shock_downstream_mach(2.0, 1.4)
        downstream_total_pressure = compute_post_shock_total_pressure(250000.0, 2.0, 1.4)

        self.assertLess(downstream_mach, 1.0)
        self.assertGreater(downstream_mach, 0.0)
        self.assertLess(downstream_total_pressure, 250000.0)

    def test_assembles_supersonic_state_from_total_conditions(self) -> None:
        gas_state = assemble_gas_state_from_total_conditions(
            x_value=0.1,
            area_value=1.5e-4,
            mach_number=1.8,
            total_pressure=250000.0,
            total_temperature=350.0,
            thermo_provider=AirThermoProvider(),
        )

        self.assertGreater(gas_state.mach_number, 1.0)
        self.assertGreater(gas_state.velocity, gas_state.thermo_state.sound_speed)


if __name__ == "__main__":
    unittest.main()