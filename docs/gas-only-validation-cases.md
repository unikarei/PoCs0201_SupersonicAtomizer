# Gas-Only Validation Cases

This document records the approved gas-only validation cases for Phase 5 Task `P5-T06`.

## Purpose

The purpose of these cases is to define the minimum gas-only reference behaviors that should be checked before droplet coupling is added.

These cases support solver sanity validation and help separate gas-solver issues from later multiphase effects.

## Required MVP Gas-Only Validation Cases

### 1. Constant-Area Gas-Only Case

#### Purpose

Provide a basic single-phase sanity case with no droplet effects and no area variation.

#### Case Characteristics

- gas only,
- constant cross-sectional area,
- valid inlet total conditions,
- valid outlet static pressure,
- no droplet transport enabled.

#### Expected Validation Focus

- solver can produce a complete gas solution,
- axial output arrays remain internally consistent,
- no droplet-related quantities are needed to validate the gas solver,
- resulting trends remain qualitatively compatible with the selected simplified formulation.

### 2. Converging/Diverging Geometry Sanity Case

#### Purpose

Provide a geometry-sensitive gas-only case that exercises the solver’s response to changing area.

#### Case Characteristics

- gas only,
- smooth converging, diverging, or converging-diverging area profile,
- valid inlet total conditions,
- valid outlet static pressure,
- no droplet transport enabled.

#### Expected Validation Focus

- solver can consume area variation consistently,
- geometry-aligned gas outputs remain stable across the domain,
- pressure, velocity, and Mach trends respond qualitatively to area variation,
- output alignment with the grid remains correct.

## Validation Reporting Expectations

For each gas-only validation case, reporting should later capture:

- case identity,
- expected qualitative trend statement,
- pass/warn/fail status,
- relevant solver diagnostics,
- notes on simplified-model limitations.

## Boundary Guidance

The following boundaries apply:

- gas-only validation should occur before full droplet coupling validation,
- gas-only validation cases should not require breakup or droplet models,
- validation should consume structured results rather than solver internals where possible.

## Open Assumptions

The following assumptions apply until later validation tasks refine the cases:

- exact numeric reference values may not be required for the MVP planning stage,
- qualitative trend validation is acceptable for early gas-only checks,
- exact test fixtures and tolerances are deferred,
- final validation workflow structure is deferred.

## What This Task Does Not Do

This task defines gas-only validation cases only. It does not yet:

- implement validation runs,
- define exact numeric tolerances,
- provide reference datasets,
- define automated reporting format,
- define droplet-coupled validation cases.

Those details belong to later approved tasks.
