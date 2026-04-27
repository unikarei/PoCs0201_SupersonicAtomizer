# Semantic Validation Rules

This document records the approved semantic validation rules for Phase 2 Task `P2-T02`.

## Purpose

The purpose of semantic validation is to reject parsed YAML inputs that are structurally present but physically invalid, inconsistent, unsupported, or incomplete for the approved MVP.

These rules apply after raw YAML parsing and after the external schema shape is recognized.

## Validation Rule Categories

### 1. Required Section Presence

The following top-level sections must be present for an MVP case:

- `fluid`
- `boundary_conditions`
- `geometry`
- `droplet_injection`

The following sections may be omitted if later defaults are defined:

- `case`
- `models`
- `outputs`

### 2. Required Field Presence

The following fields must be present for an MVP case:

#### `fluid`

- `working_fluid`

#### `boundary_conditions`

- `Pt_in`
- `Tt_in`
- `Ps_out`

#### `geometry`

- `x_start`
- `x_end`
- `n_cells`
- `area_distribution`

#### `geometry.area_distribution`

- `type`
- `x`
- `A`

#### `droplet_injection`

- `droplet_velocity_in`
- `droplet_diameter_mean_in`
- `droplet_diameter_max_in`

### 3. Allowed Value Rules

The following enumerated values are valid in the MVP unless later tasks expand them:

- `fluid.working_fluid` must be `air` or `steam`
- `geometry.area_distribution.type` must be `table`

Additional model selectors may later be validated against explicit registries.

### 4. SI Unit Expectations

All numeric inputs are assumed to be in SI units.

Examples:

- pressure values in Pa,
- temperature values in K,
- axial coordinates in m,
- area values in $m^2$,
- velocity values in m/s,
- droplet diameters in m,
- mass flow rate in kg/s.

Inputs that are obviously intended for a different unit system should be rejected rather than silently converted.

### 5. Positive and Physical Quantity Rules

The following must be strictly positive where supplied:

- `Pt_in`
- `Tt_in`
- `Ps_out`
- `droplet_diameter_mean_in`
- `droplet_diameter_max_in`
- `water_mass_flow_rate` if supplied
- `water_mass_flow_rate_percent` if supplied
- every value in `geometry.area_distribution.A`

The following additional physical consistency rules apply:

- `droplet_diameter_max_in` must be greater than or equal to `droplet_diameter_mean_in`
- `critical_weber_number` must be positive if supplied
- `breakup_factor_mean` must be positive if supplied
- `breakup_factor_max` must be positive if supplied

### 6. Grid Extent Rules

The axial grid definition must satisfy all of the following:

- `x_end` must be greater than `x_start`
- `n_cells` must be an integer greater than zero
- the implied domain length must be positive

### 7. Area Data Rules

The tabulated area definition must satisfy all of the following:

- `geometry.area_distribution.x` and `geometry.area_distribution.A` must have the same length
- both arrays must be non-empty
- the table must contain at least two points
- every `A` value must be positive
- the `x` values in the area table must be strictly increasing
- the first and last table coordinates must be consistent with the declared geometry extent or be explicitly supported later by interpolation rules

### 8. Boundary-Condition Consistency Rules

The boundary-condition definition must satisfy all of the following:

- inlet total pressure and temperature must be physically meaningful and positive
- outlet static pressure must be physically meaningful and positive
- obviously contradictory or incomplete boundary combinations should be rejected

Detailed closure-specific checks are deferred to gas-solver tasks.

### 9. Fluid-Specific Rules

The following fluid-specific validation rules apply in the MVP:

- `inlet_wetness` is allowed mainly for steam cases
- if `working_fluid` is `air`, `inlet_wetness` should be omitted or explicitly treated as unsupported unless later defaults define behavior
- if `working_fluid` is `steam`, `steam_property_model` may be supplied and later validated against supported backends

### 10. Output Configuration Rules

If output control fields are supplied:

- `output_directory` must be a string
- `write_csv`, `write_json`, and `generate_plots` must be boolean values

### 11. Failure Handling Guidance

Semantic validation failures should be reported as configuration errors with actionable messages that identify:

- the offending field or section,
- the invalid value when practical,
- the expected constraint.

## Open Validation Assumptions

The following assumptions apply until later tasks refine validation behavior:

- no automatic unit conversion is performed,
- unsupported optional fields are rejected rather than ignored when ambiguous,
- model-selector validation is intentionally lightweight until model registries are defined,
- solver-specific consistency checks beyond configuration boundaries are deferred.

## What This Task Does Not Do

This task defines semantic validation rules only. It does not yet:

- implement validation code,
- define defaults,
- define typed internal models,
- define interpolation behavior in detail,
- define solver-side numerical bounds checks.

Those details belong to later approved tasks.
