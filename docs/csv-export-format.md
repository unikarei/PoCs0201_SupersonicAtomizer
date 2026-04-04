# CSV Export Content and Format

This document records the approved CSV export content and format for Phase 8 Task `P8-T02`.

## Purpose

The purpose of this document is to specify flat-file tabular output behavior for simulation results.

## Export Role

The CSV writer should serialize the primary axial numerical result fields into a flat, row-oriented format suitable for engineering review and downstream analysis.

## Required Columns

The CSV export should include columns for at least:

- `x`
- `A`
- `pressure`
- `temperature`
- `density`
- `working_fluid_velocity`
- `Mach_number`
- `droplet_velocity`
- `slip_velocity`
- `droplet_mean_diameter`
- `droplet_maximum_diameter`
- `Weber_number`

Where available, CSV may also include:

- breakup flag,
- droplet Reynolds number.

## Column Ordering Guidance

The CSV format should use a stable documented column order.

Recommended grouping:

1. axial/geometry fields,
2. gas fields,
3. droplet transport fields,
4. breakup-related fields,
5. optional derived quantities.

## Naming Guidance

Column names should:

- remain human-readable,
- remain stable across runs,
- match the documented schema vocabulary where practical,
- avoid hidden unit conversion or ambiguous abbreviations.

## File Naming Guidance

The CSV artifact should follow the documented run-artifact conventions and remain distinguishable from JSON and plot outputs.

## Boundary Guidance

The following boundaries apply:

- the CSV writer consumes the structured output result schema,
- the CSV writer must not recompute solver quantities,
- metadata and diagnostics may be handled separately if they do not fit naturally into the flat table.

## What This Task Does Not Do

This task defines CSV export behavior only. It does not yet:

- define JSON structure,
- define plotting behavior,
- define output failure handling in detail,
- implement CSV writing code.

Those details belong to later approved tasks.
