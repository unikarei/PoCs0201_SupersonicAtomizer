# Gas Solver Formulation Boundaries

This document records the approved gas solver formulation boundaries for Phase 5 Task `P5-T02`.

## Purpose

The purpose of this document is to clarify what the MVP quasi-1D gas solver does and does not attempt to model.

These boundaries keep the solver aligned with the approved scope and prevent premature expansion into non-MVP physics.

## Included Formulation Scope

The MVP gas solver formulation includes:

- steady quasi-1D internal compressible flow,
- axial variation along a prescribed one-dimensional geometry,
- gas-state evolution using the selected thermo abstraction,
- computation of pressure, temperature, density, velocity, and Mach number,
- use of a prescribed cross-sectional area distribution $A(x)$.

## Formulation Characteristics

The gas solver formulation should assume:

- one-dimensional axial treatment,
- cross-sectionally averaged flow quantities,
- prescribed geometry rather than geometry-fluid interaction,
- solver-side use of a thermo-provider abstraction,
- one-way coupling with droplets in the MVP.

## Explicitly Excluded from the MVP Gas Solver

The gas solver must not attempt to model:

- 2D or 3D CFD,
- shock-resolving multiphase CFD,
- high-fidelity turbulence modeling,
- full multiphase feedback from droplets to gas,
- detailed external free-jet behavior,
- wall-film effects,
- droplet collision or coalescence effects,
- non-equilibrium condensation,
- full optimization workflows.

## Coupling Boundary

For the MVP:

- gas affects droplets,
- droplet feedback to the gas is neglected,
- gas solving and droplet solving remain sequential rather than iteratively coupled.

## Thermo Boundary

The gas solver formulation must:

- depend on the thermo abstraction,
- avoid hard-coding air or steam formulas directly into solver orchestration,
- remain compatible with a future IF97-ready steam backend.

## Numerical Simplicity Preference

The MVP formulation should prefer:

- transparent equations,
- stable and reproducible updates,
- conservative scope,
- clear diagnostics over model complexity.

## Open Assumptions

The following assumptions remain open for later tasks:

- exact closure details for inlet/outlet condition handling,
- the degree of choking-aware behavior required by approved cases,
- whether losses are excluded entirely in the MVP executable implementation,
- exact marching versus iterative realization.

## What This Task Does Not Do

This task defines formulation boundaries only. It does not yet:

- define the exact state-update sequence,
- define boundary-condition closure logic in detail,
- define numerical failure criteria in detail,
- implement the gas solver,
- define validation cases in detail.

Those details belong to later approved tasks.
