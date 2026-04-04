# MVP Plot Set

This document records the approved MVP plot set for Phase 8 Task `P8-T04`.

## Purpose

The purpose of this document is to lock the minimum required visual outputs from the approved specification.

## Required Plots

At minimum, the plotting layer should generate plots versus `x` for:

- pressure,
- temperature,
- working fluid velocity,
- droplet velocity,
- Mach number,
- droplet mean diameter,
- droplet maximum diameter,
- Weber number.

## Plotting Expectations

The MVP plot set should satisfy all of the following:

- plots are generated from structured result data,
- plot naming remains stable and understandable,
- axis meaning remains explicit,
- the selected plot set covers both gas and droplet behavior,
- breakup-driving behavior is visible through the Weber-number plot.

## File Output Guidance

Plot artifacts should be written as static image files compatible with the documented run-artifact conventions.

## Boundary Guidance

The following boundaries apply:

- plotting consumes structured result objects only,
- plotting must not recompute solver quantities,
- styling remains separate from physics and solver logic.

## Open Assumptions

The following assumptions remain open for later approved work:

- whether some variables are combined into multi-panel figures,
- exact figure sizes and style defaults,
- exact file naming for individual plot artifacts.

## What This Task Does Not Do

This task defines the required MVP plot set only. It does not yet:

- define the full plotting input contract,
- define output/plotting failure behavior,
- implement plotting code.

Those details belong to later approved tasks.
