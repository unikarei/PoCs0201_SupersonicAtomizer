# Area Profile Abstraction

This document records the approved area profile abstraction for Phase 3 Task `P3-T02`.

## Purpose

The purpose of the area profile abstraction is to separate downstream solver use of cross-sectional area from the original input format used in configuration.

The abstraction must allow the gas solver and related layers to query area consistently along the axial coordinate without knowing whether the source came from tabulated YAML input or another future geometry source.

## Core Abstraction Concept

The geometry layer should later expose a conceptually independent `AreaProfile` abstraction.

### Role

`AreaProfile` should provide a stable interface for area-related queries along the axial coordinate while hiding the raw source representation.

It should support downstream consumers such as:

- the gas solver,
- the grid layer when geometry sampling is needed,
- diagnostics or validation logic that needs area lookup.

## Required Capabilities

The abstraction should support at least the following conceptual operations.

### 1. Query Area at Axial Position

Recommended capability:

- `area_at(x)`

#### Purpose

Return the cross-sectional area corresponding to axial position `x`.

#### Notes

- this is the primary geometry query required by the quasi-1D solver,
- returned values must remain in SI units,
- exact interpolation behavior is deferred to the next task.

### 2. Expose Domain Support

Recommended capabilities:

- `x_min`
- `x_max`
- `supports(x)`

#### Purpose

Allow downstream logic to understand the valid query range for the area profile.

#### Notes

- `supports(x)` should conceptually indicate whether a query lies within the supported axial domain,
- this helps separate geometry validity checks from solver logic.

### 3. Preserve Source Metadata

Recommended metadata:

- `profile_type`
- `source_points`
- `is_tabulated`

#### Purpose

Preserve traceability of the original area source without forcing downstream consumers to use raw configuration structures.

## Abstraction Requirements

The area profile abstraction should satisfy all of the following:

- it must be independent of raw YAML parsing,
- it must be independent of solver-specific state,
- it must provide consistent area lookup along $x$,
- it must preserve SI-unit area values,
- it must allow future source forms beyond tabulated input,
- it must remain reusable across gas solver, validation, and diagnostics logic.

## Boundary Guidance

The following boundary rules apply:

- the gas solver should consume `AreaProfile` queries rather than raw `x`/`A` arrays,
- configuration code may provide source data but should not act as the geometry query layer,
- interpolation details should remain inside geometry-related modules rather than solver modules,
- plotting should consume solved result data rather than query geometry directly for physics reconstruction.

## Relationship to Other Geometry Concepts

The area profile abstraction is distinct from:

- `GeometryConfig`, which preserves validated input configuration,
- `GeometryModel`, which represents the broader axial domain and metadata,
- `AxialGrid`, which represents computational discretization,
- interpolation policy, which defines how tabulated area data is evaluated between points.

## MVP Assumptions

The following assumptions apply until later tasks refine behavior:

- the MVP source form is tabulated area data,
- the abstraction should still be designed to allow future analytic or alternate profile sources,
- out-of-range query behavior will be defined separately from the abstraction itself,
- interpolation behavior is not finalized in this task.

## What This Task Does Not Do

This task defines the abstraction only. It does not yet:

- define interpolation rules,
- define exact error behavior for out-of-range queries,
- implement Python interfaces or classes,
- define grid sampling rules,
- implement geometry diagnostics.

Those details belong to later approved tasks.
