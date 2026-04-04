# Axial Geometry Representation

This document records the approved axial geometry representation for Phase 3 Task `P3-T01`.

## Purpose

The purpose of the axial geometry representation is to define how the internal duct/nozzle domain is represented before grid generation and area-profile interpolation are implemented.

The geometry representation must provide a stable internal description of the axial domain and the user-supplied area profile required by the quasi-1D solver.

## Core Representation Concept

The geometry layer should represent the internal flow path as a one-dimensional axial domain with a prescribed cross-sectional area distribution $A(x)$.

This representation is geometry-focused only. It should not contain gas-solver state, droplet state, or plotting logic.

## Recommended Internal Geometry Model

The geometry layer should later expose a model conceptually equivalent to `GeometryModel`.

### Role

`GeometryModel` should provide the validated geometry information needed by:

- the grid layer,
- the gas solver,
- the droplet solver indirectly through the gas solution,
- result assembly and diagnostics where geometry metadata is needed.

## Required Geometry Contents

The internal geometry representation should include at least the following information.

### 1. Axial Range

The geometry model should include:

- `x_start`
- `x_end`
- `length`

#### Notes

- `length` should be derivable from `x_end - x_start`.
- The axial range defines the physical one-dimensional simulation domain.

### 2. Area Profile Source

The geometry model should preserve the origin of the area data.

Recommended fields:

- `area_profile_type`
- `area_profile_data`

#### MVP Expectation

For the MVP, `area_profile_type` should correspond to tabulated data.

`area_profile_data` should preserve the validated source information needed for later interpolation, including:

- tabulated `x` coordinates,
- tabulated `A` values.

### 3. Geometry Metadata

The geometry model should include metadata useful to downstream layers without embedding solver behavior.

Recommended metadata fields:

- `domain_label`
- `source_description`
- `is_tabulated_profile`

#### Notes

- metadata is optional but useful for diagnostics and result traceability,
- metadata must not be used as a substitute for physical geometry data.

## Geometry Representation Requirements

The geometry representation should satisfy all of the following:

- it represents a single axial domain for one case,
- it preserves SI-unit geometry inputs,
- it keeps area information separate from numerical grid generation,
- it is suitable for later interpolation queries,
- it is solver-independent and reusable across downstream modules.

## Boundary Guidance

The following boundary rules apply:

- the geometry representation must not parse raw YAML directly,
- the geometry representation must not generate the computational grid,
- the geometry representation must not contain gas or droplet solver state,
- the geometry representation must not perform plotting or file IO,
- the geometry representation must preserve enough information for later area queries.

## Relationship to Other Model Groups

The axial geometry representation is distinct from:

- `GeometryConfig`, which represents validated configuration input,
- `AxialGrid`, which represents the computational discretization,
- `AreaProfile`, which will later define area-query behavior,
- gas and droplet solution models.

## Open Assumptions

The following assumptions apply until later geometry and grid tasks refine the details:

- the domain is one-dimensional along the axial coordinate only,
- the geometry is stationary during simulation,
- one area profile is sufficient for one case,
- tabulated area data is the only required MVP source form,
- interpolation behavior is deferred to later tasks.

## What This Task Does Not Do

This task defines the axial geometry representation only. It does not yet:

- define interpolation rules,
- define the area-profile query interface in detail,
- define axial grid generation,
- implement Python geometry classes,
- implement geometry diagnostics.

Those details belong to later approved tasks.
