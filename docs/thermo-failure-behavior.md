# Thermo Failure Behavior

This document records the approved thermo failure behavior for Phase 4 Task `P4-T05`.

## Purpose

The purpose of this document is to ensure that thermodynamic property failures are surfaced clearly and do not become ambiguous solver failures.

Thermo failures must remain identifiable as thermo-layer issues whenever the root cause is invalid property access, unsupported backend capability, or out-of-range thermo state behavior.

## Failure Categories

The thermo layer should explicitly surface failures for at least the following categories.

### 1. Invalid State Requests

Use when a thermo query requests a nonphysical or unsupported thermodynamic state.

Examples:

- nonpositive temperature,
- nonpositive pressure,
- impossible state combinations,
- requests outside the provider’s supported state subset.

### 2. Backend Absence or Unavailability

Use when the requested thermo backend cannot be provided.

Examples:

- requested steam backend is not installed,
- provider implementation is unavailable,
- backend dependency cannot be initialized.

### 3. Out-of-Range State Queries

Use when a provider recognizes the query form but the requested state lies outside the backend’s valid domain.

Examples:

- IF97 region request outside supported bounds,
- temperature/pressure combinations beyond validated provider range,
- backend-specific state-domain violations.

### 4. Unsupported Phase-Region Requests

Use when a state requires phase-region behavior the selected provider or MVP does not support.

Examples:

- unsupported wet-steam region request,
- unsupported phase-boundary query,
- non-equilibrium request against an equilibrium-only provider.

## Reporting Requirements

Thermo failures should report, where practical:

- the provider or backend involved,
- the requested fluid,
- the offending query inputs,
- the type of failure,
- whether the issue is unsupported, unavailable, or nonphysical.

## Propagation Guidance

Thermo failures should:

- remain distinguishable from generic numerical failures,
- propagate upward with context from the application layer,
- be summarized cleanly by the CLI,
- avoid hidden fallback behavior.

## Boundary Guidance

The following boundaries apply:

- the gas solver must not swallow thermo failures and continue ambiguously,
- configuration/model-selection code must not relabel backend absence as generic solver failure,
- IO and plotting must never trigger primary thermo-provider behavior.

## Relationship to Error Taxonomy

These failures should align with the approved error taxonomy and remain distinct from:

- configuration errors,
- model-selection errors,
- numerical solver failures,
- output errors.

## Open Assumptions

The following assumptions apply until later implementation tasks refine the behavior:

- exact exception-class hierarchy is deferred,
- exit-code mapping is deferred,
- backend-specific failure payload shape is deferred,
- some failures may later be wrapped with case/run context by the application layer.

## What This Task Does Not Do

This task defines thermo failure behavior only. It does not yet:

- implement exception classes,
- define concrete backend dependency handling,
- define CLI formatting,
- define retry behavior,
- define logging configuration.

Those details belong to later approved tasks.
