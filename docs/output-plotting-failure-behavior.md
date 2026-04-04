# Output and Plotting Failure Behavior

This document records the approved output and plotting failure behavior for Phase 8 Task `P8-T06`.

## Purpose

The purpose of this document is to ensure export and plotting issues are distinguishable from solver issues and are reported with the expected run-summary behavior.

## Failure Categories

The output and plotting layers should explicitly distinguish at minimum:

- CSV write failures,
- JSON write failures,
- plot-generation failures,
- output-path or directory failures,
- serialization-shape mismatches where relevant.

## Separation from Solver Failures

Output and plotting failures must remain distinguishable from:

- input/configuration errors,
- thermo failures,
- gas-solver failures,
- droplet-solver failures,
- breakup-model failures.

## Reporting Expectations

When an output or plotting failure occurs, reporting should include as much of the following as practical:

- artifact type,
- target path or artifact context,
- failure category,
- concise failure summary,
- run-summary impact.

## Run-Summary Guidance

The application run summary should be able to indicate whether:

- simulation solved successfully but one or more outputs failed,
- serialization completed but plotting failed,
- all requested outputs completed successfully.

## Boundary Guidance

The following boundaries apply:

- IO owns serialization and file-writing failures,
- plotting owns figure-generation failures,
- application orchestration aggregates these outcomes into run summary behavior,
- solver layers must not hide output-layer issues.

## Open Assumptions

The following assumptions remain open for later approved work:

- whether some output failures are warnings versus fatal errors,
- exact exception types used by the implementation,
- whether partial artifact success is acceptable under some run modes.

## What This Task Does Not Do

This task defines output and plotting failure behavior only. It does not yet:

- implement exception classes,
- implement writers or plotters,
- define CLI formatting in detail,
- define retry behavior.

Those details belong to later approved tasks.
