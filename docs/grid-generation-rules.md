# Grid Generation Rules

This document records the approved grid generation rules for Phase 3 Task `P3-T05`.

## Purpose

The purpose of these rules is to define how a valid and reproducible axial grid is constructed from validated case inputs.

These rules apply after geometry/config validation and before solver execution.

## Inputs to Grid Generation

Grid generation should consume validated geometry-related inputs, including:

- `x_start`
- `x_end`
- `n_cells`
- the validated axial geometry/domain representation

The grid-generation step should not consume gas-state, droplet-state, or plotting information.

## Extent Validation Rules

Before generating the grid, the following conditions must hold:

- `x_end` must be greater than `x_start`
- domain length `x_end - x_start` must be strictly positive
- the geometry domain must be internally consistent with the selected area profile support

If these conditions are not satisfied, grid generation must fail explicitly.

## Cell Count Handling

The MVP grid-generation rules should interpret `n_cells` as the number of axial cells or intervals across the domain.

### Required Rules

- `n_cells` must be an integer
- `n_cells` must be greater than zero
- `node_count` should therefore be `n_cells + 1`

### Rationale

This interpretation provides:

- explicit interval count for marching,
- a clear relationship between cells and nodes,
- consistent inclusion of both domain endpoints.

## Endpoint Inclusion Rules

The generated grid should include both physical domain endpoints.

That means:

- the first node must be located at `x_start`
- the last node must be located at `x_end`

This ensures direct alignment between the declared geometry domain and solver evaluation range.

## MVP Spacing Rule

For the MVP, grid generation should default to **uniform spacing** across the domain.

### Uniform Grid Rule

For a valid domain and cell count:

- compute a constant spacing $\Delta x = \frac{x_{end} - x_{start}}{n_{cells}}$
- generate ordered nodes spanning the closed interval $[x_{start}, x_{end}]$

### Rationale

Uniform spacing is preferred for the MVP because it is:

- simple,
- reproducible,
- easy to test,
- consistent with the MVP preference for transparent numerics.

Support for non-uniform grids may be added later as an extension.

## Ordering and Reproducibility Rules

Generated grid nodes must satisfy all of the following:

- node positions are strictly increasing,
- the grid is deterministic for the same validated inputs,
- spacing is internally consistent with the chosen generation rule,
- endpoint values are preserved exactly in intent.

## Failure Conditions

Grid generation should fail explicitly if any of the following are encountered:

- invalid domain extent,
- non-integer `n_cells`,
- nonpositive `n_cells`,
- inconsistent geometry/domain information,
- generated nodes that are not strictly ordered,
- generated spacing that is nonpositive.

These failures should be reported as configuration or geometry/grid-generation errors rather than hidden solver failures.

## Boundary Guidance

The following architectural boundaries apply:

- grid generation belongs to the grid layer,
- geometry validation should occur before grid generation,
- solver modules should consume the generated grid rather than recreate it,
- plotting and IO should use output/result data aligned to the generated grid, not regenerate the grid independently.

## Open Assumptions

The following assumptions apply until later tasks refine the implementation:

- the MVP uses one shared axial grid for gas and droplet calculations,
- the MVP uses uniform spacing only,
- floating-point implementation details for endpoint construction may be handled later,
- adaptive or geometry-weighted grid refinement is out of scope for the MVP.

## What This Task Does Not Do

This task defines grid generation rules only. It does not yet:

- implement grid generation code,
- define geometry/grid diagnostics in detail,
- define adaptive refinement,
- define solver marching formulas,
- define performance optimizations for large grids.

Those details belong to later approved tasks.
