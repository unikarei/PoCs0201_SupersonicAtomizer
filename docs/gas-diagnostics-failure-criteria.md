# Gas Diagnostics and Failure Criteria

This document records the approved gas-solver diagnostics and failure criteria for Phase 5 Task `P5-T05`.

## Purpose

The purpose of this document is to make gas-solver numerical problems visible, actionable, and distinct from configuration or thermo-layer errors.

Gas-solver failures must surface clearly enough to support debugging, validation, and robust CLI reporting.

## Diagnostic Categories

The gas solver should explicitly diagnose at least the following categories.

### 1. Nonphysical State Diagnostics

Use when the solver encounters states such as:

- negative pressure,
- nonpositive temperature,
- nonpositive density,
- invalid Mach number,
- NaN or infinite state values.

These conditions should be treated as fatal solver failures.

### 2. Branch Ambiguity Diagnostics

Use when the solver cannot determine a physically acceptable branch unambiguously.

Examples:

- multiple mathematically plausible solutions,
- unresolved choking-related branch choices,
- inconsistent branch behavior across the domain.

These conditions should be surfaced explicitly rather than hidden.

### 3. Failed Closure Diagnostics

Use when the solver cannot satisfy the intended boundary-condition closure or update requirements.

Examples:

- inability to reconcile inlet and outlet conditions under the selected formulation,
- failure to produce a valid local state during axial advancement,
- failure of a required iteration or update process.

### 4. Incomplete Solution Progression Diagnostics

Use when the solver cannot validly complete the axial solution.

Examples:

- termination before the final axial node,
- valid solution only up to an intermediate location,
- breakdown of update logic after partial progress.

## Warning Guidance

Warnings may later be used for non-fatal quality concerns, but the following MVP cases should generally be treated as fatal:

- nonphysical states,
- failed closure,
- unresolved branch ambiguity,
- incomplete domain progression.

## Required Failure Context

When a gas-solver failure occurs, diagnostics should include as much of the following as practical:

- axial location,
- offending variable names,
- last valid state summary,
- selected model or provider names,
- likely cause category.

## Reporting Guidance

Gas diagnostics should remain distinct from:

- input/configuration errors,
- thermo backend failures,
- droplet-solver failures,
- output/plotting errors.

The application layer may later enrich gas failures with case context, but the root solver issue should remain identifiable.

## What This Task Does Not Do

This task defines gas diagnostics and failure criteria only. It does not yet:

- implement diagnostic objects,
- define numerical tolerances,
- define CLI formatting,
- define retry behavior,
- define solver validation cases.

Those details belong to later approved tasks.
