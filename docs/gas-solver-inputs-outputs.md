# Gas Solver Inputs and Outputs

This document records the approved gas solver contract for Phase 5 Task `P5-T01`.

## Purpose

The purpose of this document is to formalize the gas solver contract relative to the grid, geometry, thermo abstraction, and boundary conditions.

The gas solver contract must define what information the solver consumes and what axial outputs it must produce for the MVP.

## Gas Solver Inputs

The gas solver should consume validated internal models and abstractions only.

### Required Input Groups

- `AxialGrid`
- `GeometryModel`
- `AreaProfile`
- `BoundaryConditionConfig`
- thermo provider abstraction
- relevant run/config metadata needed for diagnostics

### Input Responsibilities

#### 1. Grid Input

The solver requires:

- ordered axial node positions,
- spacing information,
- grid metadata needed for marching or evaluation.

#### 2. Geometry Input

The solver requires:

- axial domain extent,
- area-profile support along the domain,
- geometry consistency already validated before solver entry.

#### 3. Thermo Input

The solver requires a thermo provider that can supply:

- density,
- sound speed,
- enthalpy or equivalent energy property,
- supported thermodynamic state evaluation.

#### 4. Boundary Condition Input

The solver requires:

- inlet total pressure `Pt_in`,
- inlet total temperature `Tt_in`,
- outlet static pressure `Ps_out`.

## Gas Solver Outputs

The gas solver must produce an ordered axial solution suitable for downstream droplet transport, output writing, plotting, and validation.

### Required Primary Axial Outputs

The solver must provide, as functions of $x$:

- `pressure`
- `temperature`
- `density`
- `velocity`
- `mach_number`

### Required Structural Outputs

The gas solver output should also preserve:

- `x` or `x_values`
- `area` or `area_values`
- ordered local gas states
- gas-solver diagnostics

## Recommended Output Model

The solver output should be representable as a `GasSolution` containing:

- local `GasState` entries,
- aligned axial arrays,
- diagnostics metadata.

## Output Requirements

The gas solver output should satisfy all of the following:

- values are aligned with the axial grid,
- values remain in SI units,
- output arrays are mutually consistent in length,
- outputs are suitable for downstream droplet-solver consumption,
- diagnostics remain attached without mixing them into physical arrays.

## Boundary Guidance

The following boundaries apply:

- the gas solver must not parse raw YAML,
- the gas solver must consume geometry/grid/thermo abstractions rather than raw external data,
- the gas solver output must remain separate from droplet and breakup outputs,
- output writers and plotters should consume `GasSolution`-compatible structures rather than recomputing gas quantities.

## Open Assumptions

The following assumptions apply until later gas-solver tasks refine details:

- one gas solution is produced over one shared axial grid,
- one-way coupling applies in the MVP, so droplet feedback is absent,
- exact solver formulation details are deferred to later tasks,
- optional auxiliary outputs may be added later if needed for diagnostics.

## What This Task Does Not Do

This task defines gas solver inputs and outputs only. It does not yet:

- define the exact quasi-1D formulation,
- define the solver marching sequence,
- define numerical failure criteria in detail,
- implement gas-solver code,
- define droplet coupling behavior beyond the gas-output contract.

Those details belong to later approved tasks.
