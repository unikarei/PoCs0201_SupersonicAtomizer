# Defaults Policy

This document records the approved configuration defaults policy for Phase 2 Task `P2-T07`.

## Purpose

The purpose of this policy is to make configuration defaults explicit, centralized, and auditable before configuration code is implemented.

Defaults must be applied only in the config layer after schema and semantic validation. They must not be hidden inside solver, plotting, thermo, or IO modules.

## Defaulting Principles

- Default only fields that are genuinely optional for the MVP.
- Do not default physically essential boundary conditions or geometry inputs.
- Prefer explicit user input for physics-critical parameters where ambiguity could hide modeling assumptions.
- Keep defaults stable, documented, and easy to override.

## Fields That Must Not Be Defaulted

The following inputs are required and must not be silently defaulted:

- `fluid.working_fluid`
- `boundary_conditions.Pt_in`
- `boundary_conditions.Tt_in`
- `boundary_conditions.Ps_out`
- `geometry.x_start`
- `geometry.x_end`
- `geometry.n_cells`
- `geometry.area_distribution`
- `droplet_injection.droplet_velocity_in`
- `droplet_injection.droplet_diameter_mean_in`
- `droplet_injection.droplet_diameter_max_in`

## Allowed MVP Defaults

### 1. Drag Model

- Field: `models.drag_model`
- Default: `standard_sphere`
- Rationale: the spec allows a simple spherical drag model as the MVP baseline.

### 2. Breakup Model

- Field: `models.breakup_model`
- Default: `weber_critical`
- Rationale: the MVP breakup behavior is a simple Weber-threshold model.

### 3. Critical Weber Number

- Field: `models.critical_weber_number`
- Default: repository-defined MVP default value
- Rationale: the spec permits this parameter to be defaulted when not explicitly provided.
- Note: the exact numeric default should be introduced later in code/config defaults, not hard-coded in this document.

### 4. Output Enablement

- Field: `outputs.write_csv`
- Default: `true`
- Rationale: CSV export is a core MVP deliverable.

- Field: `outputs.write_json`
- Default: `true`
- Rationale: JSON export is a core MVP deliverable.

### 5. Plotting Behavior

- Field: `outputs.generate_plots`
- Default: `true`
- Rationale: plotting is a required MVP capability and should be enabled by default unless explicitly disabled.

### 6. Output Directory

- Field: `outputs.output_directory`
- Default: `outputs`
- Rationale: aligns with the approved run-artifact conventions.

### 7. Wetness Handling

- Field: `fluid.inlet_wetness`
- Default: omitted / `None`
- Rationale: wetness is optional and mainly relevant for steam cases.
- Handling rule:
  - if omitted, it remains unset rather than forced to a physical value,
  - later semantic/config logic may interpret omission differently for `air` and `steam`.

## Fields That May Remain Optional Without Immediate Defaults

The following fields may remain optional at this stage and may be left unset unless later tasks require concrete defaults:

- `models.breakup_factor_mean`
- `models.breakup_factor_max`
- `models.steam_property_model`
- `droplet_injection.water_mass_flow_rate`
- `case.name`
- `case.description`
- `case.config_version`

## Default Application Rules

- Apply defaults only after semantic validation succeeds.
- Preserve explicit user-provided values over defaults.
- Do not invent defaults for unsupported model names or invalid inputs.
- Defaults should be represented centrally in config-layer logic later.
- Default application should be visible in translated internal configuration, not hidden in downstream modules.

## Open Defaulting Assumptions

The following assumptions apply until later tasks refine concrete config behavior:

- exact numeric default values may be defined later for configurable model parameters,
- omitted wetness is preferable to assuming a physical wetness value,
- output defaults should support the MVP user experience without requiring extra YAML fields,
- optional model parameters should remain unset unless a clear documented default is needed.

## What This Task Does Not Do

This task defines policy only. It does not yet:

- implement a defaults module,
- define concrete numeric constants in code,
- define how defaults are displayed in CLI summaries,
- define provider-specific thermo defaults,
- define writer-specific file-format defaults beyond output enablement.

Those details belong to later approved tasks.
