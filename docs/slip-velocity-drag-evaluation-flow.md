# Slip Velocity and Drag Evaluation Flow

This document records the approved slip-velocity and drag evaluation flow for Phase 6 Task `P6-T03`.

## Purpose

The purpose of this document is to specify the local calculation sequence required to update droplet motion using gas-state inputs.

## Core Local Quantities

The droplet update flow should use local access to:

- gas velocity,
- gas density,
- gas pressure and temperature where needed,
- droplet velocity,
- droplet diameter metrics,
- model parameters needed by the drag evaluation.

## Local Evaluation Sequence

At each axial location or step, the droplet solver should conceptually proceed through the following sequence.

### Step 1. Gas-State Lookup

- obtain the local gas state from `GasSolution`,
- ensure alignment with the current axial droplet state,
- use structured gas-state access rather than recomputing gas quantities.

### Step 2. Slip-Velocity Evaluation

- compute slip velocity from the local difference between gas velocity and droplet velocity,
- preserve sign handling explicitly,
- allow zero-slip and near-zero-slip cases to remain well defined.

### Step 3. Drag Input Preparation

- gather the local quantities required by the drag model,
- include droplet size information,
- include any fluid properties required by the selected drag formulation,
- prepare model inputs without embedding drag-specific formulas across the solver.

### Step 4. Drag Evaluation

- call the drag-model abstraction,
- obtain the drag response needed for the droplet update,
- preserve a clean boundary between transport logic and drag correlation details.

### Step 5. Droplet Motion Update

- use the evaluated drag response to update droplet velocity,
- preserve axial consistency with the selected marching strategy,
- keep the droplet state update aligned with the shared grid.

### Step 6. Derived Quantity Preparation

- update slip-dependent derived quantities such as Weber number at the correct stage,
- prepare any diagnostic values needed for later checks,
- preserve consistency between updated droplet state and local gas data.

## Flow Requirements

The slip and drag evaluation flow should satisfy all of the following:

- use the gas solution as the upstream source of gas data,
- keep drag logic behind a dedicated abstraction,
- preserve SI-unit consistency,
- detect invalid local states close to the evaluation point,
- remain compatible with later breakup integration.

## Boundary Guidance

The following boundaries apply:

- the droplet solver must not reconstruct or re-solve the gas field,
- the thermo layer remains the owner of fluid-property evaluation,
- the drag model remains replaceable,
- breakup decisions are deferred to later approved tasks.

## Open Assumptions

The following assumptions remain open for later approved tasks:

- the exact drag coefficient expression used by the MVP default model,
- whether Reynolds number is always evaluated or only when required,
- the exact timing of breakup application relative to derived droplet metrics.

## What This Task Does Not Do

This task defines the slip-velocity and drag evaluation flow only. It does not yet:

- define the full drag-model abstraction contract,
- define the full axial marching strategy,
- define diagnostics and bounds checks in full detail,
- implement droplet update code.

Those details belong to later approved tasks.
