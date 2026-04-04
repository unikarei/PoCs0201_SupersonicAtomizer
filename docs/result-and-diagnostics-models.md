# Result and Diagnostics Models

This document records the approved result and diagnostics models for Phase 2 Task `P2-T05`.

## Purpose

The purpose of these models is to standardize how final simulation outputs, warnings, validation status, and output artifact metadata are represented after solver execution.

These models sit downstream of configuration translation and solver-state evolution. They provide the stable data contracts consumed by IO, plotting, validation reporting, and CLI summaries.

## Model Set Overview

The result/diagnostics layer should define the following internal models:

- `SimulationResult`
- `RunDiagnostics`
- `ValidationReport`
- `OutputMetadata`

## 1. `SimulationResult`

Top-level combined result model for one simulation run.

### Role

`SimulationResult` aggregates the output-ready information from the gas solution, droplet solution, case metadata, model selections, and diagnostics.

### Expected Fields

- `case_name`
- `working_fluid`
- `gas_solution`
- `droplet_solution`
- `diagnostics`
- `validation_report`
- `output_metadata`

### Notes

- `SimulationResult` should be the primary object consumed by writers and plotters.
- It should not require downstream consumers to reconstruct solver state manually.
- It should remain independent of raw YAML layout.

## 2. `RunDiagnostics`

Structured diagnostics model for one run.

### Role

`RunDiagnostics` represents warnings, numerical notes, failure context, and overall solver status.

### Expected Fields

- `status`
- `warnings`
- `messages`
- `failure_category`
- `failure_location`
- `last_valid_state_summary`

### Notes

- `status` may later distinguish values such as success, warning, or failure.
- `failure_category` should align with the approved error taxonomy.
- `last_valid_state_summary` should remain lightweight and human-readable.

## 3. `ValidationReport`

Structured validation-summary model for one run.

### Role

`ValidationReport` represents validation outcomes after the simulation completes.

### Expected Fields

- `status`
- `checks_run`
- `checks_passed`
- `checks_warned`
- `checks_failed`
- `observations`

### Notes

- Validation reporting should remain distinct from solver diagnostics.
- The report should support sanity checks and later reference-case validation.
- Observations should capture concise trend-based findings when available.

## 4. `OutputMetadata`

Structured artifact and output-traceability model.

### Role

`OutputMetadata` represents where run artifacts were written and what output choices were applied.

### Expected Fields

- `run_id`
- `output_directory`
- `csv_path`
- `json_path`
- `diagnostics_path`
- `plot_paths`
- `write_csv`
- `write_json`
- `generate_plots`

### Notes

- Artifact names and directory structure should align with the approved run-artifact conventions.
- `plot_paths` may later be a mapping from plot name to path.
- This model should remain focused on artifact metadata rather than physical results.

## Boundary Guidance

The following boundary rules apply to these models:

- result models must not perform solver computations,
- diagnostics must remain distinct from physical state arrays,
- validation reporting must remain distinct from numerical failure handling,
- output metadata must describe artifact locations without duplicating writer logic.

## Relationship to Other Model Groups

These models are distinct from:

- case configuration models,
- solver state models,
- geometry/grid runtime models,
- error taxonomy definitions.

They serve as the output-facing aggregation layer after solver execution.

## What This Task Does Not Do

This task defines result and diagnostics model structure only. It does not yet:

- implement Python dataclasses or typed classes,
- define writer file formats in detail,
- define CSV column ordering,
- define plot generation behavior,
- implement validation execution.

Those details belong to later approved tasks.
