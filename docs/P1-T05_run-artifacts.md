# Run Artifact Conventions

This document records the approved run artifact conventions for Phase 1 Task `P1-T05`.

## Purpose

The purpose of these conventions is to standardize where simulation outputs are written, how files are named, and what metadata should accompany each run before output-writing code is implemented.

## Output Root

- Default top-level artifact directory: `outputs/`
- Each simulator run should write into a dedicated run directory beneath `outputs/`.

## Run Directory Convention

Recommended run-directory pattern:

- `outputs/<run_id>/`

Where `run_id` should be a filesystem-safe identifier. A timestamp-based identifier is acceptable later, but the exact generation method is deferred.

## Recommended Run Layout

Each run directory should support the following layout:

```text
outputs/
  <run_id>/
    results.csv
    results.json
    diagnostics.json
    plots/
      pressure.png
      temperature.png
      working_fluid_velocity.png
      droplet_velocity.png
      mach_number.png
      droplet_mean_diameter.png
      droplet_maximum_diameter.png
      weber_number.png
```

## Artifact Naming Conventions

### Primary Numeric Outputs

- CSV results file: `results.csv`
- JSON results file: `results.json`

### Diagnostics and Run Metadata

- Diagnostics and run-summary file: `diagnostics.json`

This file should later be able to include:

- run identifier,
- case path or case label,
- selected model names,
- warning/error summary,
- validation summary status,
- execution timestamps when available.

### Plot Outputs

Plots should live in a `plots/` subdirectory.

Recommended filenames:

- `pressure.png`
- `temperature.png`
- `working_fluid_velocity.png`
- `droplet_velocity.png`
- `mach_number.png`
- `droplet_mean_diameter.png`
- `droplet_maximum_diameter.png`
- `weber_number.png`

## Naming Rules

- Use lowercase snake_case filenames.
- Use stable names for standard outputs.
- Avoid embedding spaces in artifact names.
- Keep file naming independent of the internal solver implementation.
- Keep directory naming deterministic once `run_id` selection is defined.

## Metadata Guidance

A run should later carry enough metadata to support traceability, including:

- run identifier,
- input case reference,
- working fluid,
- selected thermo backend,
- selected breakup model,
- grid summary,
- solver status,
- warning count and error summary.

## What This Task Does Not Do

This task defines conventions only. It does not yet:

- implement output writers,
- define the full JSON schema,
- define CSV column order,
- define plotting code,
- define diagnostics object models.

Those details belong to later approved tasks.
