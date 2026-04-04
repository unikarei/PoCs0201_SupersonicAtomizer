# JSON Export Content and Format

This document records the approved JSON export content and format for Phase 8 Task `P8-T03`.

## Purpose

The purpose of this document is to specify structured machine-readable output behavior for simulation results.

## Export Role

The JSON writer should serialize the full structured simulation result, including metadata, settings summary, numerical results, and diagnostics.

## Required Top-Level Content

The JSON export should include at minimum:

- metadata,
- settings summary,
- numerical results,
- diagnostics.

## Numerical Results Content

The numerical results portion should include aligned axial arrays for at least:

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

Where available, JSON should also support:

- breakup flags,
- droplet Reynolds number,
- output metadata.

## Metadata and Settings Guidance

The JSON structure should preserve machine-readable summaries of:

- case identity,
- selected models,
- selected fluid and backend information,
- output settings relevant to the run.

## Diagnostics Guidance

The JSON structure should preserve diagnostics such as:

- warnings,
- run status,
- failure summaries,
- solver notes where available.

## Structure Requirements

The JSON format should satisfy all of the following:

- remain machine-readable and stable,
- preserve explicit nesting for metadata versus results versus diagnostics,
- avoid flattening away important structure,
- avoid recomputing or inferring physics during serialization.

## Boundary Guidance

The following boundaries apply:

- the JSON writer consumes the structured result schema,
- the JSON writer does not perform solver logic,
- plotting and validation should be able to consume equivalent structured content without relying on raw JSON layout internals.

## What This Task Does Not Do

This task defines JSON export behavior only. It does not yet:

- define CSV column ordering in full detail,
- define plotting behavior,
- define output failure handling in detail,
- implement JSON writing code.

Those details belong to later approved tasks.
