# Example YAML Conventions

This document records the approved example YAML conventions for Phase 10 Task `P10-T02`.

## Purpose

The purpose of this document is to ensure sample cases clearly reflect the supported schema and assumptions.

## Convention Scope

Example YAML files should make required fields, optional fields, and model-selection choices easy to identify.

## Required Field Conventions

Example YAML should clearly show required fields for:

- `working_fluid`,
- `Pt_in`,
- `Tt_in`,
- `Ps_out`,
- axial grid definition,
- tabulated `A(x)` area data,
- droplet injection fields.

## Optional Field Conventions

Example YAML should clearly distinguish optional fields such as:

- `inlet_wetness`,
- `water_mass_flow_rate`,
- `critical_weber_number`,
- `breakup_factor_mean`,
- `breakup_factor_max`,
- model-selection overrides.

## Model-Selection Clarity

Example YAML should make model-selection choices explicit for:

- thermo backend selection where applicable,
- drag model selection where applicable,
- breakup model selection.

## Readability Guidance

Example YAML should satisfy all of the following:

- remain human-readable,
- keep SI-unit expectations consistent with documentation,
- avoid ambiguous shorthand,
- keep example intent easy to understand,
- remain aligned with the documented YAML schema structure.

## Boundary Guidance

The following boundaries apply:

- examples should demonstrate only supported schema behavior,
- examples should not imply unsupported defaults that conflict with documentation,
- example clarity takes priority over compactness.

## What This Task Does Not Do

This task defines example YAML conventions only. It does not yet:

- define the user run workflow in detail,
- define developer extension guidance,
- define the assumptions and limitations summary,
- create example YAML files.

Those details belong to later approved tasks.
