# Regression Case Set

This document records the approved regression case set for Phase 9 Task `P9-T04`.

## Purpose

The purpose of this document is to prevent unintended behavior drift across refactors and later implementation changes.

## Regression Scope

Regression tracking should use a fixed set of documented reference cases and tracked outputs that remain stable across repeated runs.

## Required MVP Regression Case Categories

### 1. Gas-Only Reference Cases

Regression coverage should include:

- constant-area gas-only case,
- converging/diverging gas-only sanity case.

Tracked outputs should include representative gas solution fields and run-status outcomes.

### 2. Droplet Transport Reference Cases

Regression coverage should include:

- zero-slip or near-zero-slip droplet case,
- slip-driven acceleration droplet case.

Tracked outputs should include representative droplet velocity, slip velocity, and related transport outputs.

### 3. Breakup Reference Cases

Regression coverage should include:

- no-breakup threshold case,
- breakup-trigger case.

Tracked outputs should include representative Weber-number behavior, breakup flags, and diameter-change behavior.

## Tracked Output Guidance

Regression tracking should preserve documented expectations for:

- selected output fields,
- status or diagnostics summaries,
- qualitative trend descriptions,
- tolerances when quantitative references are later approved.

## Boundary Guidance

The following boundaries apply:

- regression cases must be fixed and documented,
- regression tracking is distinct from one-off debugging cases,
- regression tracking should use stable result structures and case identities.

## What This Task Does Not Do

This task defines the regression case set only. It does not yet:

- define storage conventions for fixtures and references,
- define automated regression tooling,
- implement regression tests.

Those details belong to later approved tasks.
