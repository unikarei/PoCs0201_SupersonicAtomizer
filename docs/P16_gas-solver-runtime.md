# Phase 16 — Quasi-1D Gas Solver Runtime

## Purpose

Implement the quasi-1D compressible gas solver that computes axial distributions of pressure, temperature, density, velocity, and Mach number using geometry, boundary conditions, and the thermo abstraction.

## Implemented Modules

| Module | File | Responsibility |
|---|---|---|
| Boundary conditions | `solvers/gas/boundary_conditions.py` | Initialize gas-side BC state from inlet/outlet conditions |
| State updates | `solvers/gas/state_updates.py` | Area-Mach relation, bisection solver, static property computation |
| Quasi-1D solver | `solvers/gas/quasi_1d_solver.py` | Axial marching and `GasSolution` assembly |
| Diagnostics | `solvers/gas/diagnostics.py` | Structured failure reporting with last-valid-state context |

## Solver Algorithm

The MVP gas solver uses an **isentropic quasi-1D area-Mach** approach:

1. **Boundary condition initialization** (`initialize_gas_boundary_conditions`):
   - Compute outlet pressure ratio: `Ps_out / Pt_in`
   - Derive outlet Mach number from isentropic relation
   - Validate subsonic outlet (M < 1)

2. **Throat area derivation:**
   - Compute area-to-throat ratio at the outlet using the outlet Mach number
   - Derive the effective throat area: `A_throat = A_outlet / f(M_outlet)`

3. **Axial marching** (node-by-node):
   - Compute local area ratio: `A(x) / A_throat`
   - Solve subsonic Mach from area ratio via **bisection** (`solve_subsonic_mach_from_area_ratio`)
   - Compute static temperature and pressure from isentropic relations
   - Evaluate thermo state for density, enthalpy, sound speed
   - Assemble `GasState` at each node

4. **Solution assembly:** Collect all `GasState` objects into a `GasSolution` with diagnostic metadata.

## Key Functions

- `compute_area_mach_relation(M, γ)` — standard quasi-1D $A/A^*$ formula
- `solve_subsonic_mach_from_area_ratio(A/A*, γ)` — bisection inversion (tol = 1e-10, max 200 iters)
- `compute_static_temperature(T_t, M, γ)` — isentropic temperature relation
- `compute_static_pressure(P_t, M, γ)` — isentropic pressure relation
- `assemble_gas_state(...)` — combine Mach, thermo state, and velocity into `GasState`

## Failure Handling

- `raise_gas_solver_failure()` — raises `NumericalError` with category, location, and last-valid-state summary
- Checks: area ratio ≤ 1 (branch ambiguity), nonphysical states, incomplete progression

## Limitations

- **Subsonic foundation path only** — no choking-aware or supersonic branch selection
- **Isentropic** — no friction, heat transfer, or loss models
- **Constant γ** — relies on thermo provider's `heat_capacity_ratio` attribute

## Test Files

- `tests/test_runtime_gas_solver_scaffold.py`
- `tests/test_runtime_gas_boundary_conditions.py`
- `tests/test_runtime_gas_state_updates.py`
- `tests/test_runtime_quasi_1d_gas_solver.py`
- `tests/test_runtime_gas_diagnostics.py`

## Tasks Covered

| Task | Title |
|---|---|
| P16-T01 | Create gas solver runtime module scaffold |
| P16-T02 | Implement gas boundary-condition initialization |
| P16-T03 | Implement quasi-1D gas-state update utilities |
| P16-T04 | Implement axial gas solver for supported executable cases |
| P16-T05 | Implement gas diagnostics and failure propagation |
