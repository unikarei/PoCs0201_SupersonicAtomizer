# Contract Tests for Swappable Interfaces

This document records the approved contract-test plan for Phase 9 Task `P9-T03`.

## Purpose

The purpose of this document is to protect the extensibility promises made for swappable thermo and breakup interfaces.

## Contract Test Scope

Contract tests should verify that all concrete implementations of a shared interface satisfy the same behavioral expectations.

## Required Contract-Test Targets

### 1. Thermo Providers

Contract tests should cover all thermo providers against the common thermo interface.

Expected checks include:

- required interface methods or operations are present,
- valid-state evaluation succeeds for supported states,
- invalid-state handling is explicit,
- returned values and metadata remain compatible with SI-unit expectations,
- backend-specific behavior does not violate shared contracts.

### 2. Breakup Models

Contract tests should cover all breakup models against the common breakup-model interface.

Expected checks include:

- required interface inputs and outputs are honored,
- no-breakup and triggered-breakup outcomes are surfaced consistently,
- diagnostic outputs remain structured and explicit,
- unsupported or invalid inputs fail explicitly rather than silently.

## Contract-Test Guidance

The contract-test plan should satisfy all of the following:

- verify interface conformance independent of one specific implementation,
- preserve swappability promises,
- remain deterministic,
- keep model-specific extensions from breaking shared behavior.

## Boundary Guidance

The following boundaries apply:

- thermo and breakup implementations are tested against their interface contracts,
- contract tests are narrower than full integration tests,
- contract tests are distinct from physics-validation cases.

## What This Task Does Not Do

This task defines contract-test expectations only. It does not yet:

- define regression case tracking,
- define test-data storage conventions,
- implement contract-test code for runtime modules.

Those details belong to later approved tasks.
