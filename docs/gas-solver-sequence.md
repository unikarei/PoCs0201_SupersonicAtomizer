# Gas Solver Sequence and State Update Logic

This document records the approved gas solver sequence for Phase 5 Task `P5-T03`.

## Purpose

The purpose of this document is to provide a clear implementation path for advancing the gas solution along the axial domain.

The sequence defined here is conceptual and intended to guide a later small, testable implementation.

## High-Level Sequence

The gas solver should proceed through the following conceptual steps.

1. receive validated inputs,
2. initialize inlet-side state representation,
3. evaluate geometry/area support along the grid,
4. advance or assemble gas states along the axial domain,
5. evaluate derived quantities such as Mach number,
6. assemble the final `GasSolution`,
7. attach diagnostics and completion status.

## Detailed Step Sequence

### Step 1. Accept Validated Inputs

Consume:

- `AxialGrid`,
- geometry/area abstractions,
- `BoundaryConditionConfig`,
- thermo provider,
- any required solver settings.

### Step 2. Establish Initial/Reference State

Use the inlet-side boundary information to establish the initial or reference gas-state basis needed for solution advancement.

This step should remain consistent with the later boundary-condition handling design.

### Step 3. Evaluate Local Geometry Support

For each relevant axial location:

- query area information through the geometry abstraction,
- ensure the area value is available and valid,
- align geometry sampling with the axial grid.

### Step 4. Advance Gas State Along the Domain

For each axial step or evaluation location:

- use the selected thermo provider as needed,
- update or solve for local pressure, temperature, density, and velocity,
- preserve numerical consistency with the quasi-1D formulation,
- detect and surface nonphysical states immediately.

### Step 5. Compute Derived Quantities

After or during local gas-state evaluation:

- compute Mach number using velocity and sound speed,
- preserve any additional diagnostics required for solver status.

### Step 6. Store Ordered Local States

As the solution advances:

- store local `GasState` entries in axial order,
- preserve aligned arrays for output-ready quantities,
- maintain consistency between state history and grid coordinates.

### Step 7. Finalize Solution Object

At the end of the domain traversal:

- assemble the final `GasSolution`,
- attach diagnostics,
- mark solver status as complete, warned, or failed depending on outcome.

## State Update Logic Guidance

The implementation should later preserve the following logic expectations:

- updates occur in axial order,
- each local gas state is consistent with the thermo abstraction,
- derived quantities are computed from validated local state data,
- failure checks occur close to the update point,
- the final solution remains aligned with the grid.

## Boundary Guidance

The following boundaries apply:

- the gas solver must not parse raw configuration,
- geometry interpolation details remain outside solver logic,
- thermo-property calculations remain behind the thermo provider,
- droplet transport begins only after the gas solution is available.

## Open Assumptions

The following assumptions apply until later implementation tasks refine the sequence:

- the solver may later use a marching or iterative realization,
- exact initialization details depend on boundary-condition closure,
- choking-aware branching may be added if needed by approved cases,
- solver-specific intermediate variables are intentionally omitted here.

## What This Task Does Not Do

This task defines gas solver sequence and update logic conceptually. It does not yet:

- define the exact quasi-1D equations,
- define boundary-condition closure logic in full,
- define numerical tolerances,
- implement solver code,
- define gas-only validation cases.

Those details belong to later approved tasks.
