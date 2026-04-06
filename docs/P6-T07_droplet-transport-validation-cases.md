# Droplet Transport Validation Cases

This document records the approved droplet transport validation cases for Phase 6 Task `P6-T07`.

## Purpose

The purpose of these cases is to establish baseline droplet-transport validation before breakup effects are enabled.

These cases help separate transport behavior from later breakup behavior.

## Required MVP Droplet Transport Validation Cases

### 1. Zero-Slip or Near-Zero-Slip Case

#### Purpose

Provide a droplet transport case in which the initial relative velocity is zero or very small.

#### Case Characteristics

- valid gas solution,
- droplet transport enabled,
- injection velocity equal or nearly equal to local gas velocity,
- valid positive droplet diameters,
- breakup effects not required for validation.

#### Expected Validation Focus

- slip velocity remains zero or near zero initially,
- drag-driven acceleration remains minimal when relative motion is minimal,
- the solver preserves stable droplet-state evolution,
- breakup is not needed to validate the transport update flow.

### 2. Slip-Driven Acceleration Case

#### Purpose

Provide a droplet transport case with a meaningful gas-droplet relative velocity that should produce observable drag-driven acceleration.

#### Case Characteristics

- valid gas solution,
- droplet transport enabled,
- finite initial gas-droplet slip,
- valid positive droplet diameters,
- breakup effects not required for the baseline transport check.

#### Expected Validation Focus

- slip velocity is evaluated correctly,
- drag response produces qualitatively expected droplet acceleration,
- droplet velocity evolves consistently along the axial grid,
- derived transport quantities remain internally consistent.

## Validation Reporting Expectations

For each droplet transport validation case, reporting should later capture:

- case identity,
- expected qualitative trend statement,
- pass/warn/fail status,
- relevant transport diagnostics,
- notes on simplified-model limitations.

## Boundary Guidance

The following boundaries apply:

- these validation cases focus on transport behavior before breakup,
- these cases should consume structured gas and droplet results where possible,
- breakup-specific validation belongs to the next phase.

## Open Assumptions

The following assumptions apply until later validation tasks refine the cases:

- exact numeric tolerances are deferred,
- qualitative trend validation is acceptable at this planning stage,
- exact fixture files and reference datasets are deferred,
- exact automated reporting format is deferred.

## What This Task Does Not Do

This task defines droplet transport validation cases only. It does not yet:

- implement validation runs,
- define breakup-trigger validation,
- provide numeric benchmark datasets,
- define automated reporting format.

Those details belong to later approved tasks.
