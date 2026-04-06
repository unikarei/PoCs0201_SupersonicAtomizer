# Output Result Schema

This document records the approved output result schema for Phase 8 Task `P8-T01`.

## Purpose

The purpose of this document is to standardize the final data contract consumed by CSV writers, JSON writers, plotters, and validation/reporting components.

## Schema Role

The final output schema should represent a `SimulationResult`-compatible structure assembled from gas, droplet, breakup, metadata, and diagnostics content.

## Required Core Axial Fields

The output schema must include aligned axial fields for at least:

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

## Additional Useful MVP Fields

Where available, the schema should also support:

- breakup event indicator or flag,
- derived droplet Reynolds number,
- run metadata,
- settings summary,
- diagnostics and status summary.

## Metadata Requirements

The output schema should preserve metadata such as:

- case identity,
- selected working fluid,
- selected thermo backend,
- selected drag model,
- selected breakup model,
- run artifact metadata where needed.

## Diagnostics Requirements

The output schema should preserve diagnostics separately from physical arrays.

This should include, where available:

- warnings,
- failure context,
- run status,
- solver completion notes.

## Schema Requirements

The output result schema should satisfy all of the following:

- axial arrays are aligned in length,
- values remain in SI units,
- metadata is structured and machine-readable,
- diagnostics are explicit and separate from numerical fields,
- writers and plotters can consume the result without recomputing physics.

## Boundary Guidance

The following boundaries apply:

- solvers produce structured gas, droplet, and breakup outputs,
- result assembly combines these into one output-ready structure,
- IO and plotting consume structured results only,
- validation reads stable result structures rather than raw solver internals.

## What This Task Does Not Do

This task defines the output result schema only. It does not yet:

- define CSV column ordering in detail,
- define JSON layout in detail,
- define the MVP plot list in detail,
- define output failure behavior in detail,
- implement result serialization code.

Those details belong to later approved tasks.
