# Tabulated Area Interpolation Behavior

This document records the approved tabulated area interpolation behavior for Phase 3 Task `P3-T03`.

## Purpose

The purpose of this policy is to define how user-provided tabulated area data $(x, A)$ is evaluated between data points for the MVP geometry layer.

This behavior applies to tabulated area profiles only. It standardizes solver-facing area lookup while keeping interpolation details inside geometry-related modules.

## MVP Interpolation Method

The MVP interpolation method should be **piecewise linear interpolation** between adjacent tabulated points.

### Rationale

Piecewise linear interpolation is preferred for the MVP because it is:

- simple,
- transparent,
- numerically stable,
- easy to validate,
- consistent with the MVP preference for readable and conservative numerics.

## In-Domain Evaluation Rules

For a query point $x_q$ lying within the supported tabulated domain:

- if $x_q$ exactly matches a tabulated coordinate, return the corresponding tabulated area value,
- if $x_q$ lies strictly between two adjacent tabulated coordinates, return the linearly interpolated area value between those two points.

The interpolation should use only the bracketing interval containing the query point.

## Boundary Behavior

For the MVP, supported area queries should be limited to the declared profile domain.

### At the Lower Boundary

- if $x_q = x_{min}$, return the first tabulated area value.

### At the Upper Boundary

- if $x_q = x_{max}$, return the last tabulated area value.

### Outside the Supported Domain

- interpolation outside the supported domain should not silently extrapolate,
- out-of-range queries should be treated as unsupported geometry queries and surfaced explicitly,
- any future extrapolation support would require an explicit design change.

## Monotonicity Expectations

The tabulated axial coordinates must be strictly increasing.

Specifically:

- duplicate `x` values are invalid,
- descending or non-monotone `x` sequences are invalid,
- interpolation logic may assume a strictly ordered table after validation succeeds.

No monotonicity requirement is imposed on area values themselves.

That means:

- converging profiles are allowed,
- diverging profiles are allowed,
- converging-diverging profiles are allowed,
- non-monotone area variation is allowed as long as all area values remain physically valid.

## Invalid Input Rules

The following tabulated inputs are invalid for interpolation:

- `x` and `A` arrays with different lengths,
- empty arrays,
- fewer than two tabulated points,
- nonpositive area values,
- duplicate `x` coordinates,
- non-increasing `x` sequences,
- unsupported profile type for the interpolation implementation.

These invalid conditions should be detected before solver use.

## Numerical Expectations

The interpolation policy should satisfy the following:

- preserve SI-unit area values,
- avoid hidden smoothing or curve fitting,
- preserve the original tabulated values at tabulated coordinates,
- remain deterministic for the same input table and query point.

## Boundary Guidance

The following architectural boundaries apply:

- interpolation belongs to geometry-related modules, not the gas solver,
- configuration validation should reject invalid tables before interpolation is used,
- solver code should consume area queries without owning interpolation details,
- plotting code should not be responsible for defining geometry interpolation policy.

## Open Assumptions

The following assumptions apply until later tasks refine the implementation:

- interpolation is one-dimensional along the axial coordinate only,
- no higher-order interpolation is needed for the MVP,
- no extrapolation is permitted in the MVP,
- tolerance rules for floating-point boundary matching may be defined later in implementation.

## What This Task Does Not Do

This task defines interpolation behavior only. It does not yet:

- implement interpolation code,
- define the exact query API implementation,
- define geometry diagnostics in code,
- define grid sampling strategy,
- define performance optimizations for large tables.

Those details belong to later approved tasks.
