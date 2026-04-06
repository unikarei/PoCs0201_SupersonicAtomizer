from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.solvers.gas import (
    GasBoundaryConditionState,
    assemble_gas_state,
    compute_area_mach_relation,
    compute_static_pressure,
    compute_static_temperature,
    create_gas_solver_diagnostics,
    initialize_gas_boundary_conditions,
    solve_quasi_1d_gas_flow,
    solve_subsonic_mach_from_area_ratio,
)


class TestRuntimeGasSolverScaffold(unittest.TestCase):
    def test_gas_solver_runtime_exports_exist(self) -> None:
        self.assertTrue(callable(initialize_gas_boundary_conditions))
        self.assertTrue(callable(compute_area_mach_relation))
        self.assertTrue(callable(solve_subsonic_mach_from_area_ratio))
        self.assertTrue(callable(compute_static_pressure))
        self.assertTrue(callable(compute_static_temperature))
        self.assertTrue(callable(assemble_gas_state))
        self.assertTrue(callable(create_gas_solver_diagnostics))
        self.assertTrue(callable(solve_quasi_1d_gas_flow))
        self.assertTrue(hasattr(GasBoundaryConditionState, "__dataclass_fields__"))


if __name__ == "__main__":
    unittest.main()