# Droplet Marching and Update Strategy

This document records the approved droplet marching and update strategy for Phase 6 Task `P6-T05`.

## Purpose

The purpose of this document is to ensure droplet states advance consistently along the axial grid and to define the expected ordering of key droplet evaluations.

## Marching Basis

For the MVP, the droplet solver should advance representative droplet states along the same axial grid used by the gas solution.

## Axial Update Sequence

At a conceptual level, the droplet solver should proceed in axial order using the following sequence.

1. identify the current axial location,
2. obtain the aligned local gas state,
3. evaluate slip velocity,
4. prepare and evaluate drag response,
5. update droplet velocity,
6. update or preserve droplet diameter metrics as appropriate for the current phase,
7. compute derived quantities such as Weber number,
8. store the local `DropletState`,
9. continue to the next axial location.

## Ordering Requirements

The droplet marching logic should preserve the following ordering expectations:

- gas-state lookup occurs before local droplet transport evaluation,
- slip velocity is evaluated before drag-driven update,
- droplet velocity update occurs before any derived quantity that depends on the updated state when that dependency is required,
- Weber number evaluation is performed in a clearly defined position within the update flow,
- diameter-related evaluations remain explicit rather than hidden.

## Alignment Requirements

The marching strategy should satisfy all of the following:

- droplet outputs remain aligned with the axial grid,
- droplet outputs remain aligned with the gas solution,
- partial updates do not silently corrupt state ordering,
- stored local states remain internally consistent.

## MVP Boundary Guidance

The following boundaries apply:

- the droplet marching strategy remains one-dimensional,
- the gas solution is treated as an upstream dependency,
- breakup integration details are deferred to Phase 7,
- no full population-balance transport is introduced.

## Open Assumptions

The following assumptions remain open for later approved work:

- the exact discrete integration formula,
- the exact staging of breakup application relative to stored state,
- whether additional intermediate states are needed for stability.

## What This Task Does Not Do

This task defines the droplet marching strategy only. It does not yet:

- define the breakup integration sequence,
- define diagnostics and bounds checks in full detail,
- define numerical tolerances,
- implement axial marching code.

Those details belong to later approved tasks.
