# Test Data Organization

This document records the approved test-data organization plan for Phase 9 Task `P9-T05`.

## Purpose

The purpose of this document is to keep test cases, reference results, fixtures, and validation artifacts manageable as implementation proceeds.

## Organization Scope

Test data organization should define storage and naming conventions for:

- unit fixtures,
- integration cases,
- regression references,
- validation artifacts.

## Storage Guidance

A clear structure should later support separation of:

- lightweight unit-test fixtures,
- end-to-end case inputs,
- stored regression references,
- validation notes or expected trend artifacts.

## Naming Guidance

Naming conventions should preserve:

- stable case identity,
- clear distinction between air and steam cases,
- clear distinction between gas-only, transport, and breakup scenarios,
- predictable mapping between input cases and stored references.

## Management Guidance

Test data organization should satisfy all of the following:

- keep fixtures small where possible,
- avoid mixing unrelated case categories,
- preserve deterministic reuse across tests,
- support future comparison against stored reference outputs,
- remain understandable to future contributors.

## Boundary Guidance

The following boundaries apply:

- unit fixtures should remain lightweight,
- integration and regression cases may use richer case files,
- validation artifacts should remain distinct from production outputs,
- test-data organization should not leak into solver logic.

## What This Task Does Not Do

This task defines test-data organization only. It does not yet:

- define example user-facing case documentation,
- implement fixture directories or case files,
- implement automated comparison tooling.

Those details belong to later approved tasks.
