# Phase 17 — Droplet Transport Runtime

## Purpose

Implement representative droplet transport: drag-model abstraction, droplet initialization, per-step velocity updates driven by gas-droplet slip, and axial marching to produce a `DropletSolution` aligned with the gas solution.

## Implemented Modules

| Module | File | Responsibility |
|---|---|---|
| Drag models | `solvers/droplet/drag_models.py` | `DragModel` ABC, `StandardSphereDragModel`, structured I/O |
| Update helpers | `solvers/droplet/updates.py` | `initialize_droplet_state()`, `update_droplet_state()`, Weber helper |
| Transport solver | `solvers/droplet/transport_solver.py` | Axial marching with optional breakup integration |
| Diagnostics | `solvers/droplet/diagnostics.py` | State validation, failure reporting, state summaries |

## Drag Model

### `StandardSphereDragModel`

- Inputs: `StandardSphereDragInputs` (gas density, slip velocity, droplet diameter, dynamic viscosity)
- Outputs: `DragEvaluation` (Reynolds number, drag coefficient, acceleration)
- Correlation: Schiller-Naumann — $C_D = \frac{24}{Re}(1 + 0.15\,Re^{0.687})$
- Water droplet density: 1000 kg/m³ (default)
- Zero slip → zero acceleration (no-op path)

### Drag Abstraction

`DragModel` ABC with `evaluate(inputs) → DragEvaluation` — allows future replacement by alternative correlations.

## Droplet Update Sequence

1. **Initialize** at inlet (`initialize_droplet_state`):
   - Set velocity from injection config
   - Compute initial slip, drag evaluation, Weber number
   - Validate state bounds

2. **Per-step update** (`update_droplet_state`):
   - Compute slip velocity = gas velocity − droplet velocity
   - Evaluate drag acceleration
   - Estimate time step: `dt = dx / max(|u_gas|, ε)`
   - Update velocity: `u_d += a_drag · dt`
   - Recompute slip, Weber, Reynolds
   - Validate updated state

## Transport Solver (`solve_droplet_transport`)

- Marches along all gas solution nodes
- Optional breakup integration via `_apply_breakup_model()` at each step
- Returns `DropletSolution` with full axial histories and diagnostic metadata
- Catches exceptions at each step and reports with location and last-valid-state context

## Constants

- `WATER_SURFACE_TENSION = 0.072 N/m` — used for Weber number evaluation
- `dynamic_viscosity = 1.8e-5 Pa·s` — default in drag inputs

## Diagnostics

- `validate_droplet_state()` — checks finite velocity (≥ 0), positive diameters, max ≥ mean, finite Weber/Reynolds
- `raise_droplet_solver_failure()` — `NumericalError` with category, location, last-valid-state summary

## Test Files

- `tests/test_runtime_droplet_solver_scaffold.py`
- `tests/test_runtime_standard_sphere_drag.py`
- `tests/test_runtime_droplet_updates.py`
- `tests/test_runtime_droplet_transport_solver.py`
- `tests/test_runtime_droplet_diagnostics.py`

## Tasks Covered

| Task | Title |
|---|---|
| P17-T01 | Create droplet runtime module scaffold |
| P17-T02 | Implement standard-sphere drag model runtime path |
| P17-T03 | Implement droplet initialization and local update utilities |
| P17-T04 | Implement axial droplet transport solver |
| P17-T05 | Implement droplet diagnostics and failure propagation |
