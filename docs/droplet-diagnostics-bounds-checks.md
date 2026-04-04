# Droplet Diagnostics and Bounds Checks

This document records the approved droplet diagnostics and bounds checks for Phase 6 Task `P6-T06`.

## Purpose

The purpose of this document is to catch unstable or nonphysical droplet states early and to keep droplet-solver failure behavior explicit.

## Diagnostic Categories

The droplet solver should explicitly check at least the following categories.

### 1. Velocity Checks

Use when the solver encounters:

- negative droplet velocity where the selected formulation treats it as invalid,
- NaN or infinite droplet velocity,
- abrupt or inconsistent velocity updates that indicate invalid state progression.

### 2. Diameter Checks

Use when the solver encounters:

- nonpositive mean droplet diameter,
- nonpositive maximum droplet diameter,
- maximum diameter smaller than mean diameter when that is invalid for the selected state definition,
- NaN or infinite diameter values.

### 3. Slip and Derived-Quantity Checks

Use when the solver encounters:

- invalid slip velocity values,
- invalid Weber number values,
- invalid derived Reynolds-related quantities where present.

### 4. State-Consistency Checks

Use when the solver encounters:

- inconsistent droplet metrics across the same axial location,
- array-length mismatches,
- invalid transition from one axial state to the next.

## Failure Guidance

The droplet solver should surface these issues explicitly rather than silently clipping or hiding them.

## Required Failure Context

When droplet-solver failure occurs, diagnostics should include as much of the following as practical:

- axial location,
- offending droplet variables,
- last valid droplet state summary,
- related gas-state context where useful,
- likely cause category.

## Boundary Guidance

The following boundaries apply:

- config validation owns input validity before solver entry,
- the droplet solver owns runtime droplet-state validity,
- breakup-specific checks may later extend these diagnostics but should remain distinguishable,
- CLI formatting remains outside the solver.

## Open Assumptions

The following assumptions remain open for later approved work:

- exact warning-versus-failure thresholds,
- whether some negative-velocity states are physically admissible in special cases,
- the exact structure of droplet diagnostic objects.

## What This Task Does Not Do

This task defines droplet diagnostics and bounds checks only. It does not yet:

- define breakup diagnostics,
- define validation cases in detail,
- define CLI reporting format,
- implement runtime checks.

Those details belong to later approved tasks.
