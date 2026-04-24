# Test Data Organization

This document describes organization of test data and fixtures.

Required items:

- unit fixtures
- integration cases
- reference-case naming conventions

Store integration fixtures and reference outputs under `tests/data` with clear identifiers.

Maintain a list of **regression references** (reference outputs) alongside integration cases for CI comparisons.

- Keep associated validation artifacts (plots, CSV reference outputs) alongside integration cases for validation and regression checks.

- Test-data suites should include representative air and steam cases to cover both thermo backends (air and steam cases).

- Validation artifacts and test-data conventions should be documented clearly and `should not leak into solver logic` — test helpers must remain separate from solver code.