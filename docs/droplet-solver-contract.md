# Droplet Solver Contract

This document records the approved droplet solver contract for Phase 6 Task `P6-T01`.

## Purpose

The purpose of this document is to formalize how the droplet solver consumes gas results and droplet injection inputs and what droplet-side outputs it must produce for the MVP.

## Solver Role

The droplet solver is responsible for:

- initializing droplet state from validated case inputs,
- consuming the gas solution produced by the gas solver,
- computing slip-driven droplet evolution along the axial grid,
- preparing droplet-side outputs for later breakup, result assembly, plotting, and validation.

## Required Inputs

The droplet solver should consume validated internal models and abstractions only.

### Input Groups

- `AxialGrid`
- `GasSolution`
- `DropletInjectionConfig`
- drag-model abstraction
- breakup-model abstraction placeholder or compatible downstream boundary
- relevant model settings and diagnostics context

### Input Responsibilities

#### 1. Grid Input

The solver requires:

- ordered axial node positions,
- spacing or interval information,
- grid alignment consistent with the gas solution.

#### 2. Gas-Solution Input

The solver requires axial gas data that can provide at minimum:

- gas velocity,
- pressure,
- temperature,
- density,
- Mach-related or sound-speed-supporting data where needed,
- aligned axial coordinates.

#### 3. Droplet Injection Input

The solver requires:

- initial droplet velocity,
- initial mean droplet diameter,
- initial maximum droplet diameter,
- any injection metadata required by the MVP configuration.

## Required Outputs

The droplet solver must produce an ordered axial solution suitable for breakup evaluation, result assembly, output writing, plotting, and validation.

### Required Primary Axial Outputs

The droplet solver must provide, as functions of $x$:

- `droplet_velocity`
- `slip_velocity`
- `droplet_mean_diameter`
- `droplet_maximum_diameter`
- `Weber_number`

### Additional Useful Outputs

Where available, the solver should support:

- local droplet Reynolds number,
- breakup flags or placeholders for later breakup integration,
- droplet-solver diagnostics.

## Recommended Output Model

The solver output should be representable as a `DropletSolution` containing:

- local `DropletState` entries,
- aligned axial arrays,
- diagnostics metadata,
- any later breakup indicators.

## Contract Requirements

The droplet solver output should satisfy all of the following:

- values are aligned with the shared axial grid,
- values remain in SI units,
- outputs are mutually consistent in length,
- droplet state remains logically separate from gas state,
- diagnostics remain attached without being mixed into physical output arrays.

## Boundary Guidance

The following boundaries apply:

- the droplet solver must not parse raw YAML,
- the droplet solver must consume `GasSolution` rather than reconstruct gas physics,
- drag logic must remain behind a drag-model boundary,
- breakup logic remains a separate pluggable boundary,
- output writers and plotters should consume structured result objects rather than recomputing droplet quantities.

## Open Assumptions

The following assumptions apply until later tasks refine the details:

- droplets are represented by bulk or representative metrics rather than a full distribution,
- one-way coupling applies in the MVP,
- the droplet solver uses the same axial grid as the gas solution,
- exact breakup integration timing is deferred to Phase 7.

## What This Task Does Not Do

This task defines the droplet solver contract only. It does not yet:

- define the exact injection assumptions in detail,
- define the local slip and drag update sequence in detail,
- define the drag model abstraction in full,
- define diagnostics in full detail,
- implement droplet-solver code.

Those details belong to later approved tasks.
