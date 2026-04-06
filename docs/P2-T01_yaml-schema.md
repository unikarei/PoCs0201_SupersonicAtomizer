# YAML Schema Structure

This document records the approved raw YAML configuration structure for Phase 2 Task `P2-T01`.

## Purpose

The purpose of this document is to define a stable external configuration shape for the simulator before schema-validation and translation logic are implemented.

The YAML structure is organized by responsibility so that configuration parsing can remain separate from solver logic.

## Top-Level Sections

A simulation case should use the following top-level sections:

- `case`
- `fluid`
- `boundary_conditions`
- `geometry`
- `droplet_injection`
- `models`
- `outputs`

## Section Definitions

### 1. `case`

Repository-level case metadata.

#### Fields

| Field | Required | Type | Description |
|---|---|---|---|
| `name` | No | string | Human-readable case name |
| `description` | No | string | Optional case description |
| `config_version` | No | string or integer | Reserved for future schema versioning |

### 2. `fluid`

Working-fluid selection and fluid-specific input settings.

#### Fields

| Field | Required | Type | Description |
|---|---|---|---|
| `working_fluid` | Yes | string | `air` or `steam` |
| `inlet_wetness` | No | number | Optional wetness input, mainly for steam cases |

#### Notes

- `working_fluid` is mandatory.
- `inlet_wetness` is optional in the raw schema and may later be constrained by semantic validation rules.

### 3. `boundary_conditions`

Inlet and outlet thermodynamic boundary conditions.

#### Fields

| Field | Required | Type | Description |
|---|---|---|---|
| `Pt_in` | Yes | number | Inlet total pressure in Pa |
| `Tt_in` | Yes | number | Inlet total temperature in K |
| `Ps_out` | Yes | number | Outlet static pressure in Pa |

### 4. `geometry`

Axial domain and area-distribution definition.

#### Fields

| Field | Required | Type | Description |
|---|---|---|---|
| `x_start` | Yes | number | Axial start location in m |
| `x_end` | Yes | number | Axial end location in m |
| `n_cells` | Yes | integer | Number of axial cells or intervals |
| `area_distribution` | Yes | mapping | Area definition along the axis |

#### `geometry.area_distribution`

The MVP raw schema supports tabulated area data.

| Field | Required | Type | Description |
|---|---|---|---|
| `type` | Yes | string | Expected MVP value: `table` |
| `x` | Yes | array[number] | Axial coordinates for area table |
| `A` | Yes | array[number] | Area values corresponding to `x` |

### 5. `droplet_injection`

Representative droplet injection inputs.

#### Fields

| Field | Required | Type | Description |
|---|---|---|---|
| `droplet_velocity_in` | Yes | number | Initial droplet velocity in m/s |
| `droplet_diameter_mean_in` | Yes | number | Initial mean droplet diameter in m |
| `droplet_diameter_max_in` | Yes | number | Initial maximum droplet diameter in m |
| `water_mass_flow_rate` | No | number | Optional injected droplet mass flow rate in kg/s |

### 6. `models`

Configuration-driven model and backend selection.

#### Fields

| Field | Required | Type | Description |
|---|---|---|---|
| `drag_model` | No | string | Drag model selector |
| `breakup_model` | No | string | Breakup model selector |
| `critical_weber_number` | No | number | Breakup threshold parameter |
| `breakup_factor_mean` | No | number | Mean-diameter reduction factor |
| `breakup_factor_max` | No | number | Maximum-diameter reduction factor |
| `steam_property_model` | No | string | Steam thermo backend selector |

#### Notes

- Defaults for omitted model fields are deferred to later configuration tasks.
- Unsupported names are not handled in this document; they belong to semantic validation and model-selection logic.

### 7. `outputs`

User-facing output preferences.

#### Fields

| Field | Required | Type | Description |
|---|---|---|---|
| `output_directory` | No | string | Optional output root or target directory |
| `write_csv` | No | boolean | Enable CSV output |
| `write_json` | No | boolean | Enable JSON output |
| `generate_plots` | No | boolean | Enable plot generation |

## Example Raw YAML Shape

```yaml
case:
  name: sample_air_case
  description: Baseline quasi-1D internal-flow case
  config_version: 1

fluid:
  working_fluid: air

boundary_conditions:
  Pt_in: 600000.0
  Tt_in: 500.0
  Ps_out: 100000.0

geometry:
  x_start: 0.0
  x_end: 0.1
  n_cells: 200
  area_distribution:
    type: table
    x: [0.0, 0.03, 0.06, 0.1]
    A: [1.2e-4, 1.0e-4, 0.8e-4, 1.0e-4]

droplet_injection:
  droplet_velocity_in: 10.0
  droplet_diameter_mean_in: 100e-6
  droplet_diameter_max_in: 300e-6
  water_mass_flow_rate: 0.001

models:
  drag_model: standard_sphere
  breakup_model: weber_critical
  critical_weber_number: 12.0
  steam_property_model: if97

outputs:
  output_directory: outputs
  write_csv: true
  write_json: true
  generate_plots: true
```

## Open Schema Assumptions

The following assumptions apply until later tasks refine the configuration layer:

- one YAML file defines one simulation case,
- units are SI throughout,
- `geometry.area_distribution.type` is limited to `table` in the MVP raw schema,
- output controls remain optional,
- some optional fields may later become conditionally required through semantic validation.

## What This Task Does Not Do

This task defines the raw YAML shape only. It does not yet:

- validate values semantically,
- define defaults formally,
- implement schema parsing,
- implement translation into typed models,
- define full output JSON schema.

Those details belong to later approved tasks.
