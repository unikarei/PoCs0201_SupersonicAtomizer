from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.solvers.droplet import (
    DragEvaluation,
    DragModel,
    StandardSphereDragInputs,
    StandardSphereDragModel,
    compute_weber_number,
    create_droplet_solver_diagnostics,
    initialize_droplet_state,
    solve_droplet_transport,
    update_droplet_state,
)


class TestRuntimeDropletSolverScaffold(unittest.TestCase):
    def test_droplet_runtime_exports_exist(self) -> None:
        self.assertTrue(hasattr(StandardSphereDragInputs, "__dataclass_fields__"))
        self.assertTrue(hasattr(DragEvaluation, "__dataclass_fields__"))
        self.assertTrue(issubclass(StandardSphereDragModel, DragModel))
        self.assertTrue(callable(compute_weber_number))
        self.assertTrue(callable(create_droplet_solver_diagnostics))
        self.assertTrue(callable(initialize_droplet_state))
        self.assertTrue(callable(update_droplet_state))
        self.assertTrue(callable(solve_droplet_transport))


if __name__ == "__main__":
    unittest.main()