# MVP Example Case Set

This document records the approved MVP example case set for Phase 10 Task `P10-T01`.

## Purpose

The purpose of this document is to identify representative example cases that demonstrate the supported MVP workflow.

## Required Example Categories

At minimum, the MVP example set should include:

- one air case,
- one steam-oriented case.

## Example Case 1. Air Baseline Case

### Purpose

The air baseline case should demonstrate the standard YAML-to-result workflow using the simplest supported working-fluid path.

### Intended Coverage

This example should help demonstrate:

- working fluid selection as air,
- inlet total pressure and temperature usage,
- outlet static pressure usage,
- user-provided area profile handling,
- droplet transport and output generation in an MVP-compatible case.

## Example Case 2. Steam-Oriented Case

### Purpose

The steam-oriented case should demonstrate the thermo-abstraction path and the intended IF97-ready workflow boundary.

### Intended Coverage

This example should help demonstrate:

- working fluid selection as steam,
- thermo-backend selection behavior,
- optional inlet wetness handling where allowed,
- compatibility with the equilibrium-steam MVP assumptions,
- the same structured output workflow used by air cases.

## Example Guidance

The example case set should satisfy all of the following:

- remain aligned with approved MVP scope,
- avoid out-of-scope physics,
- use documented schema vocabulary,
- remain understandable to users as reference inputs,
- support future integration and validation use.

## Boundary Guidance

The following boundaries apply:

- examples demonstrate supported workflows only,
- examples should not silently introduce unsupported features,
- examples should remain consistent with documented assumptions and limitations.

## What This Task Does Not Do

This task defines the MVP example case set only. It does not yet:

- define exact example YAML formatting rules,
- define the user run workflow in detail,
- define developer extension guidance,
- create executable example files.

Those details belong to later approved tasks.
