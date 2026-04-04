# Thermo Contract Tests

This document records the approved thermo contract-test expectations for Phase 4 Task `P4-T06`.

## Purpose

The purpose of thermo contract tests is to verify that all thermo providers satisfy the same solver-facing expectations, regardless of the concrete fluid or backend implementation.

These tests protect swappability across air and future steam providers.

## Contract-Test Scope

Thermo contract tests should be defined for every provider intended to satisfy the shared thermo interface, including:

- the air provider,
- the steam provider path,
- future alternate steam backends.

## Required Contract-Test Expectations

### 1. Interface Conformance

Each thermo provider should satisfy the shared thermo interface contract.

Expected checks:

- required operations are present,
- required output fields can be produced,
- provider metadata is available.

### 2. SI Unit Conformance

Each provider should return values in SI units.

Expected checks:

- pressure in Pa,
- temperature in K,
- density in kg/m^3,
- enthalpy in J/kg,
- sound speed in m/s.

### 3. Supported-State Success Cases

Each provider should succeed for representative valid state queries within its supported domain.

Expected checks:

- valid air states produce consistent thermo-state outputs,
- valid steam states within the approved supported region produce consistent thermo-state outputs.

### 4. Failure Behavior Conformance

Each provider should fail explicitly for invalid or unsupported requests.

Expected checks:

- invalid state requests are rejected,
- out-of-range queries are rejected,
- unsupported phase-region requests are rejected when applicable,
- failures remain distinguishable from unrelated solver issues.

### 5. Deterministic Behavior

For the same supported query inputs, each provider should produce deterministic outputs.

Expected checks:

- repeated equivalent queries return consistent results,
- provider metadata remains stable for the same configuration.

## Provider-Specific Expectations

### Air Provider

The air provider should pass contract tests using the MVP air-property assumptions.

### Steam Provider

The steam provider should pass contract tests only within its explicitly supported MVP state subset.

The tests should not assume unsupported phase-region behavior.

## Boundary Guidance

The following boundaries apply:

- contract tests should validate interface promises, not full solver behavior,
- provider-specific internals should not be required by the contract tests,
- contract tests should remain reusable across alternate steam backends,
- gas-solver tests should remain separate from thermo contract tests.

## Open Assumptions

The following assumptions apply until later implementation tasks refine the tests:

- concrete reference states may be selected later,
- tolerance values may be defined later,
- backend availability conditions may require conditional test configuration,
- exact test-framework structure is deferred.

## What This Task Does Not Do

This task defines thermo contract-test expectations only. It does not yet:

- implement thermo tests,
- choose exact reference state values,
- define numeric tolerances,
- define backend installation strategy,
- define solver-level validation cases.

Those details belong to later approved tasks.
