# Geometry and Grid Diagnostics

This document records the approved geometry/grid diagnostics for Phase 3 Task `P3-T06`.

## Purpose

The purpose of geometry/grid diagnostics is to detect malformed geometry or invalid computational-grid conditions before solver execution begins.

These diagnostics are intended to fail early, produce actionable messages, and prevent geometry or grid issues from surfacing later as ambiguous solver failures.

## Diagnostic Scope

The geometry/grid diagnostics layer should cover:

- geometry domain validity,
- area-table validity,
- area-value validity,
- grid-generation validity,
- consistency between geometry support and generated grid.

## Required Diagnostic Checks

### 1. Invalid Axial Range Diagnostics

The following conditions should be treated as invalid geometry/domain range diagnostics:

- `x_end <= x_start`
- nonpositive domain length
- geometry domain inconsistent with declared support expectations

Expected reporting should identify:

- the offending range values,
- the violated rule,
- the affected section or model.

### 2. Nonpositive Area Value Diagnostics

The following conditions should be treated as invalid area diagnostics:

- any area value `A <= 0`
- tabulated area values that are missing or unusable for profile construction

Expected reporting should identify:

- the offending area value when practical,
- the associated table index or location when available,
- the positive-area requirement.

### 3. Inconsistent Table Length Diagnostics

The following conditions should be treated as tabulated-profile consistency diagnostics:

- `geometry.area_distribution.x` and `geometry.area_distribution.A` lengths do not match
- either array is empty
- fewer than two usable tabulated points are available

Expected reporting should identify:

- the observed lengths,
- the minimum valid requirement,
- the affected area-profile input section.

### 4. Degenerate Grid Diagnostics

The following conditions should be treated as grid-degeneracy diagnostics:

- `n_cells <= 0`
- non-integer `n_cells`
- nonpositive grid spacing
- repeated or non-increasing generated node positions
- node count inconsistent with the selected cell-count rule

Expected reporting should identify:

- the offending grid parameter,
- the violated generation rule,
- whether the issue arose before or during grid construction.

### 5. Geometry/Profile Ordering Diagnostics

The following conditions should be treated as invalid tabulated-ordering diagnostics:

- duplicate `x` values in the area table
- non-increasing `x` sequence
- unsupported out-of-domain table support relative to the declared geometry extent when not explicitly allowed

Expected reporting should identify:

- the problematic ordering condition,
- the relevant indices or values when practical,
- the monotonicity expectation.

### 6. Geometry/Grid Consistency Diagnostics

The following conditions should be treated as geometry/grid consistency diagnostics:

- generated grid endpoints do not align with the declared domain endpoints,
- generated grid lies outside supported area-profile range,
- geometry metadata and area-profile support disagree in a way that prevents valid evaluation.

Expected reporting should identify:

- the geometry values involved,
- the grid values involved,
- the consistency rule that was violated.

## Diagnostic Severity Guidance

For the MVP, the diagnostics described in this document should generally be treated as **fatal pre-solver errors** rather than warnings.

Warnings may be added later for non-fatal geometry quality concerns, but malformed geometry or degenerate grids must not proceed into solver execution.

## Reporting Guidance

Geometry/grid diagnostics should produce actionable messages that, where practical, include:

- category of issue,
- offending field or model,
- observed value,
- expected rule,
- suggested likely correction.

## Boundary Guidance

The following architectural boundaries apply:

- geometry/grid diagnostics should occur before gas-solver execution,
- solver code should not be responsible for discovering basic malformed geometry inputs,
- configuration validation and geometry/grid diagnostics may cooperate but should remain conceptually distinct,
- plotting and output modules should not perform primary geometry/grid validation.

## Open Assumptions

The following assumptions apply until later implementation tasks refine details:

- diagnostic reporting format may later be aligned with a shared diagnostics model,
- tolerance details for floating-point comparisons may be defined later,
- additional non-fatal geometry-quality warnings are deferred,
- diagnostics remain focused on MVP tabulated geometry and uniform-grid assumptions.

## What This Task Does Not Do

This task defines geometry/grid diagnostics only. It does not yet:

- implement diagnostic code,
- define shared diagnostic object classes,
- define CLI formatting for diagnostic output,
- define tolerance constants,
- define solver-side numerical diagnostics.

Those details belong to later approved tasks.
