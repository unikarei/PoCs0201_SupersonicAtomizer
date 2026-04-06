# Integration Test Matrix

This document records the approved integration test matrix for Phase 9 Task `P9-T02`.

## Purpose

The purpose of this document is to cover end-to-end behavior across the MVP pipeline using realistic multi-module workflows.

## Integration Test Scope

Integration tests should verify that the main workflow boundaries connect correctly from configuration through result generation.

## Required MVP Integration Test Areas

### 1. YAML-to-Result Execution

Integration tests should cover:

- loading a YAML case,
- validating and translating configuration,
- producing a structured simulation result,
- preserving output-ready data structures.

### 2. Air Case Pipeline

Integration tests should cover:

- an air working-fluid selection,
- end-to-end gas and droplet workflow compatibility,
- result assembly using approved MVP models,
- output generation hooks where available.

### 3. Steam-Provider Selection Behavior

Integration tests should cover:

- steam-oriented case selection behavior,
- thermo-backend selection through configuration,
- clean provider resolution or explicit unsupported-state failure,
- preservation of the thermo abstraction boundary.

### 4. Output Generation

Integration tests should cover:

- structured result serialization to JSON,
- structured result serialization to CSV,
- plot-generation invocation from structured results,
- run-summary compatibility with output outcomes.

## Integration Test Guidance

The integration test matrix should satisfy all of the following:

- exercise multi-module behavior without collapsing into full validation studies,
- remain deterministic under fixed case inputs,
- use stable documented example or fixture cases,
- verify boundary handoff between config, solver, result assembly, and outputs.

## Boundary Guidance

The following boundaries apply:

- integration tests verify connected workflow behavior,
- integration tests do not replace isolated unit tests,
- integration tests do not replace validation cases that check physical trend expectations,
- integration tests should avoid depending on manual inspection.

## What This Task Does Not Do

This task defines the integration test matrix only. It does not yet:

- define contract tests for swappable interfaces in detail,
- define regression case tracking in detail,
- define test-data organization in detail,
- implement end-to-end test code.

Those details belong to later approved tasks.
