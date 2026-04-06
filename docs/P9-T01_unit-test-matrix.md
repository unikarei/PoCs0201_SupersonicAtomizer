# Unit Test Matrix

This document records the approved unit test matrix for Phase 9 Task `P9-T01`.

## Purpose

The purpose of this document is to map low-level modules and isolated logic to focused unit tests.

## Unit Test Scope

Unit tests should target isolated logic with minimal dependency on application orchestration, file IO, or plotting behavior.

## Required MVP Unit Test Areas

### 1. Config Validation

Unit tests should cover:

- required field presence,
- allowed-value enforcement,
- SI-unit assumptions at config boundaries,
- rejection of nonphysical pressures, temperatures, diameters, grid definitions, and area values.

### 2. Geometry Interpolation

Unit tests should cover:

- tabulated area interpolation behavior,
- boundary handling at the ends of the area table,
- invalid input detection for inconsistent or nonpositive area data.

### 3. Grid Generation

Unit tests should cover:

- grid extent validation,
- node count or discretization handling,
- degenerate or invalid grid rejection,
- reproducible axial-grid construction.

### 4. Thermo Contracts

Unit tests should cover:

- thermo-provider interface compliance,
- valid-state property evaluation,
- invalid-state failure behavior,
- consistency of supported metadata and units.

### 5. Weber Number Evaluation

Unit tests should cover:

- explicit required-input handling,
- SI-unit-compatible inputs,
- dimensionless output expectation,
- stable behavior for zero-slip or small-slip conditions.

### 6. Output Formatting

Unit tests should cover:

- stable field naming,
- output schema compatibility,
- CSV column-order formatting behavior,
- JSON structural formatting behavior.

## Unit Test Guidance

The unit test matrix should satisfy all of the following:

- isolate one small concern at a time,
- avoid dependence on interactive plotting,
- avoid dependence on CLI formatting,
- support deterministic results,
- remain aligned with documented interfaces and schema contracts.

## Boundary Guidance

The following boundaries apply:

- unit tests verify isolated module behavior,
- unit tests do not replace integration, regression, or validation cases,
- unit tests should use fixtures only where needed to keep scope small.

## What This Task Does Not Do

This task defines the unit test matrix only. It does not yet:

- define end-to-end integration tests,
- define regression case tracking,
- define test-data storage conventions in detail,
- implement production unit tests for future runtime code.

Those details belong to later approved tasks.
