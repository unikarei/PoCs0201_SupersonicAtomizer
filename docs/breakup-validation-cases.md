# Breakup Validation Cases

This document records the approved breakup validation cases for Phase 7 Task `P7-T06`.

## Purpose

The purpose of these cases is to verify expected threshold behavior and non-trigger behavior for the MVP breakup model.

## Required MVP Breakup Validation Cases

### 1. No-Breakup Case

#### Purpose

Provide a case in which the evaluated Weber number remains below the critical threshold.

#### Case Characteristics

- valid gas solution,
- valid droplet transport solution,
- `Weber_number` below `critical_weber_number`,
- breakup model enabled,
- positive droplet diameters.

#### Expected Validation Focus

- breakup is not triggered,
- diameter metrics remain unchanged by breakup logic,
- breakup flags remain false or equivalent,
- non-trigger behavior is reported consistently.

### 2. Breakup-Trigger Case

#### Purpose

Provide a case in which the evaluated Weber number exceeds the critical threshold.

#### Case Characteristics

- valid gas solution,
- valid droplet transport solution,
- `Weber_number` above `critical_weber_number`,
- breakup model enabled,
- positive pre-breakup droplet diameters.

#### Expected Validation Focus

- breakup is triggered,
- mean and maximum diameters decrease according to the configured rule,
- updated diameter metrics remain physically valid,
- breakup indicators reflect the triggered event.

## Validation Reporting Expectations

For each breakup validation case, reporting should later capture:

- case identity,
- expected threshold-behavior statement,
- pass/warn/fail status,
- relevant breakup diagnostics,
- notes on simplified-model limitations.

## Boundary Guidance

The following boundaries apply:

- these cases validate breakup behavior after transport quantities are available,
- these cases should not require advanced breakup physics,
- these cases remain within the MVP Weber-threshold scope.

## Open Assumptions

The following assumptions apply until later validation tasks refine the cases:

- exact numeric tolerances are deferred,
- qualitative threshold validation is acceptable at this planning stage,
- exact fixture files and reference data are deferred,
- exact automated reporting format is deferred.

## What This Task Does Not Do

This task defines breakup validation cases only. It does not yet:

- implement validation runs,
- define advanced breakup references,
- provide benchmark datasets,
- define automated reporting format.

Those details belong to later approved tasks.
