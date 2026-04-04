# Case Configuration Data Models

This document records the approved internal case-configuration data models for Phase 2 Task `P2-T03`.

## Purpose

The purpose of these models is to define the typed internal representation of validated case inputs after raw YAML parsing and semantic validation.

These models are internal contracts. They are intended to separate external YAML structure from the data consumed by geometry setup, thermo selection, solvers, output handling, and validation.

## Model Set Overview

The case-configuration layer should define the following internal models:

- `CaseConfig`
- `FluidConfig`
- `BoundaryConditionConfig`
- `GeometryConfig`
- `DropletInjectionConfig`
- `ModelSelectionConfig`
- `OutputConfig`

## 1. `CaseConfig`

Top-level validated configuration model for one simulation case.

### Role

`CaseConfig` aggregates the validated configuration needed by the application orchestration layer.

### Expected Fields

- `case_name`
- `case_description`
- `config_version`
- `fluid`
- `boundary_conditions`
- `geometry`
- `droplet_injection`
- `models`
- `outputs`

### Notes

- Metadata fields may remain optional.
- Component fields should refer to the typed child models defined below.

## 2. `FluidConfig`

Validated fluid-selection model.

### Role

Represents the working-fluid selection and fluid-specific configuration required before thermo backend selection.

### Expected Fields

- `working_fluid`
- `inlet_wetness`

### Notes

- `working_fluid` is required.
- `inlet_wetness` remains optional and may be conditionally constrained by later validation rules.

## 3. `BoundaryConditionConfig`

Validated thermodynamic boundary-condition model.

### Role

Represents inlet and outlet boundary conditions for the gas solver.

### Expected Fields

- `Pt_in`
- `Tt_in`
- `Ps_out`

### Notes

- Values are expected to be stored in SI units.
- This model should remain solver-agnostic and not include solver state.

## 4. `GeometryConfig`

Validated geometry-definition model.

### Role

Represents the axial extent and user-supplied area distribution required to build geometry and grid objects.

### Expected Fields

- `x_start`
- `x_end`
- `n_cells`
- `area_definition`

### Notes

- `area_definition` should preserve the validated area-profile input in a form suitable for later geometry abstraction.
- Detailed interpolation behavior belongs to geometry tasks, not this model-definition task.

## 5. `DropletInjectionConfig`

Validated droplet-injection model.

### Role

Represents initial droplet conditions used to initialize the representative droplet state.

### Expected Fields

- `droplet_velocity_in`
- `droplet_diameter_mean_in`
- `droplet_diameter_max_in`
- `water_mass_flow_rate`

### Notes

- `water_mass_flow_rate` remains optional in the current MVP planning state.
- This model should describe injection inputs only, not evolving droplet states.

## 6. `ModelSelectionConfig`

Validated model-selector and backend-selection model.

### Role

Represents configuration-driven model choices and tunable model parameters.

### Expected Fields

- `drag_model`
- `breakup_model`
- `critical_weber_number`
- `breakup_factor_mean`
- `breakup_factor_max`
- `steam_property_model`

### Notes

- Omitted values may later be filled by config defaults.
- This model should not instantiate providers directly.

## 7. `OutputConfig`

Validated output-preference model.

### Role

Represents user-selected output behavior for writers and plotting.

### Expected Fields

- `output_directory`
- `write_csv`
- `write_json`
- `generate_plots`

### Notes

- This model should capture preferences only.
- Actual artifact naming and directory conventions are handled separately by output-related tasks.

## Model Boundary Guidance

The following boundary rules apply to these models:

- configuration models should represent validated inputs only,
- they must not contain solver logic,
- they must not parse YAML directly,
- they should remain serializable and easy to inspect,
- they should be suitable for typed Python representations such as dataclasses later.

## Relationship to Other Model Groups

These configuration models are distinct from:

- solver state models,
- thermo state models,
- geometry/grid runtime models,
- results and diagnostics models.

Those model groups are defined in later tasks.

## What This Task Does Not Do

This task defines configuration model structure only. It does not yet:

- implement Python dataclasses or typed classes,
- define solver state models,
- define result models,
- define defaults behavior in code,
- define translation logic from YAML into model instances.

Those details belong to later approved tasks.
