# Config Translation Flow

This document records the approved configuration translation flow for Phase 2 Task `P2-T06`.

## Purpose

The purpose of this flow is to define the processing path from raw YAML input to validated internal configuration models.

This flow preserves the architecture requirement that:

- raw YAML is handled only by the config layer,
- semantic validation happens before solver use,
- defaults remain centralized,
- solvers consume typed internal models rather than raw external dictionaries.

## Required Processing Stages

The configuration flow should proceed through the following stages in order:

1. raw parse
2. schema validation
3. semantic validation
4. defaults application
5. translation into internal models

## Stage 1. Raw Parse

### Goal

Read the YAML file into an external in-memory representation without yet treating it as valid simulation input.

### Inputs

- YAML file path
- raw file contents

### Outputs

- parsed external mapping structure

### Responsibilities

- open and read the YAML source,
- detect file access failures,
- detect invalid YAML syntax,
- preserve the external section structure for later validation.

### Failure Category

- input parsing errors

## Stage 2. Schema Validation

### Goal

Verify that the parsed external structure matches the approved raw YAML shape.

### Inputs

- parsed external mapping structure
- documented schema expectations from [docs/yaml-schema.md](yaml-schema.md)

### Outputs

- schema-checked raw configuration structure

### Responsibilities

- verify required top-level sections where applicable,
- verify field presence at the raw schema level,
- verify basic value types,
- verify nested structure shapes such as `geometry.area_distribution`.

### Failure Category

- configuration errors

## Stage 3. Semantic Validation

### Goal

Reject structurally present inputs that are physically invalid, unsupported, inconsistent, or incomplete for the MVP.

### Inputs

- schema-checked raw configuration structure
- semantic rules from [docs/semantic-validation.md](semantic-validation.md)

### Outputs

- semantically valid raw configuration structure

### Responsibilities

- enforce allowed values,
- enforce SI-unit expectations,
- enforce positivity and physical consistency checks,
- enforce grid and area-table validity,
- enforce fluid-specific constraints.

### Failure Category

- configuration errors
- model-selection errors where selector values are unsupported

## Stage 4. Defaults Application

### Goal

Apply centrally defined defaults to optional fields after the input has passed structural and semantic validation.

### Inputs

- semantically valid raw configuration structure
- approved defaults policy

### Outputs

- normalized configuration structure with defaults populated

### Responsibilities

- populate omitted optional model selections,
- populate optional output preferences,
- preserve explicit user-provided values,
- avoid hidden behavior for ambiguous unsupported inputs.

### Notes

- Default values must come from the config layer, not solver modules.
- Defaults should remain visible and auditable.

## Stage 5. Translation into Internal Models

### Goal

Convert the normalized external configuration into typed internal configuration models.

### Inputs

- normalized configuration structure
- approved internal models from [docs/case-configuration-models.md](case-configuration-models.md)

### Outputs

- `CaseConfig`
- `FluidConfig`
- `BoundaryConditionConfig`
- `GeometryConfig`
- `DropletInjectionConfig`
- `ModelSelectionConfig`
- `OutputConfig`

### Responsibilities

- map external section names to internal model fields,
- normalize metadata naming where needed,
- construct typed internal configuration objects,
- ensure downstream layers receive stable internal contracts.

### Failure Category

- configuration errors

## Recommended Ownership by Module

The configuration layer should later separate this flow across dedicated module responsibilities:

- `loader` handles raw file reading and parse entry,
- `schema` handles raw shape validation,
- `defaults` handles centralized default values,
- `translator` handles conversion into internal models.

## Data Flow Summary

The intended data flow is:

- YAML file
- parsed raw structure
- schema-checked raw structure
- semantically valid raw structure
- normalized structure with defaults
- typed internal configuration models

## Boundary Rules

- solver modules must not parse raw YAML,
- solver modules must not apply config defaults,
- plotting and IO must consume internal/result models rather than raw config mappings,
- validation of external structure must be completed before solver orchestration begins.

## What This Task Does Not Do

This task defines the config translation flow only. It does not yet:

- implement YAML loading,
- implement schema validation code,
- implement semantic validation code,
- implement defaults in code,
- implement Python model construction.

Those details belong to later approved tasks.
