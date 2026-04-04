# Axial Grid Model

This document records the approved axial grid model for Phase 3 Task `P3-T04`.

## Purpose

The purpose of the axial grid model is to standardize the computational discretization used by the gas and droplet solvers.

The axial grid model must represent the one-dimensional evaluation/marching locations derived from the validated geometry definition while remaining separate from geometry input representation and solver state.

## Core Grid Model Concept

The grid layer should later expose a model conceptually equivalent to `AxialGrid`.

### Role

`AxialGrid` should provide the ordered axial discretization used by:

- the gas solver,
- the droplet solver,
- geometry sampling,
- result assembly,
- plotting and export alignment.

## Required Grid Contents

The axial grid model should include at least the following information.

### 1. Node Positions

Recommended fields:

- `x_nodes`
- `x_start`
- `x_end`

#### Notes

- `x_nodes` should be an ordered sequence of axial positions,
- `x_start` and `x_end` should match the represented computational domain,
- node positions must remain in SI units.

### 2. Indexing Convention

The grid model should use a consistent indexing convention.

Recommended conventions:

- node indices increase in the positive axial direction,
- the first node corresponds to the inlet-side domain start,
- the last node corresponds to the outlet-side domain end.

#### Notes

- the indexing convention should be documented once and used consistently across gas, droplet, output, and validation layers,
- later implementation may use zero-based Python indexing internally.

### 3. Spacing Information

Recommended fields:

- `dx_values`
- `nominal_dx`
- `is_uniform`

#### Notes

- `dx_values` should describe spacing between adjacent nodes,
- `nominal_dx` is useful for summaries and diagnostics,
- `is_uniform` indicates whether spacing is uniform across the domain.

### 4. Grid Size Metadata

Recommended fields:

- `node_count`
- `cell_count`
- `domain_length`

#### Notes

- `domain_length` should be consistent with `x_end - x_start`,
- `node_count` and `cell_count` should be explicit rather than inferred repeatedly downstream.

## Grid Model Requirements

The axial grid model should satisfy all of the following:

- it represents a one-dimensional ordered discretization along $x$,
- it is derived from validated geometry/config inputs,
- it is independent of gas and droplet solution values,
- it can support marching or evaluation along the domain,
- it can support result alignment across gas and droplet solutions,
- it preserves SI-unit axial coordinates and spacing.

## Boundary Guidance

The following boundary rules apply:

- the grid model must not parse raw YAML,
- the grid model must not define geometry interpolation policy,
- the grid model must not contain thermodynamic or droplet physics state,
- the grid model must not contain plotting logic,
- solver modules should consume the grid model rather than reinvent indexing or spacing conventions.

## Relationship to Other Model Groups

The axial grid model is distinct from:

- `GeometryConfig`, which describes requested geometry-related configuration,
- `GeometryModel`, which represents the physical domain and area-profile source,
- `AreaProfile`, which answers area queries along the domain,
- gas and droplet solver state models, which carry evolving physical quantities.

## Open Assumptions

The following assumptions apply until later grid tasks refine the implementation:

- one axial grid is sufficient for both gas and droplet solvers in the MVP,
- the grid may later support uniform or non-uniform spacing,
- precise grid-generation rules are deferred to the next task,
- indexing details for implementation remain separate from conceptual model requirements.

## What This Task Does Not Do

This task defines the axial grid model only. It does not yet:

- define grid generation rules,
- implement Python grid classes,
- define geometry/grid diagnostics,
- define interpolation sampling details,
- define solver update formulas.

Those details belong to later approved tasks.
