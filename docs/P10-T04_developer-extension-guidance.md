# Developer Extension Guidance

This document records the approved developer extension guidance for Phase 10 Task `P10-T04`.

## Purpose

The purpose of this document is to help future contributors add thermo providers, breakup models, and validation cases safely.

## Extension Areas

The minimum developer guidance should cover:

- thermo extensions,
- breakup-model extensions,
- validation-case extensions.

## Thermo Extension Guidance

Contributor guidance should make clear that thermo extensions must:

- comply with the thermo interface contract,
- preserve SI-unit expectations,
- surface invalid-state behavior explicitly,
- avoid coupling solver orchestration to one concrete backend.

## Breakup Extension Guidance

Contributor guidance should make clear that breakup extensions must:

- comply with the breakup-model interface,
- preserve explicit diagnostics,
- remain configuration-selectable,
- avoid embedding breakup behavior across unrelated modules.

## Validation Extension Guidance

Contributor guidance should make clear that validation extensions must:

- consume stable result models,
- remain distinct from production solver logic,
- preserve documented case identity and trend expectations,
- remain understandable and reproducible.

## Guidance Principles

Developer extension guidance should satisfy all of the following:

- preserve modular boundaries,
- preserve swappability promises,
- avoid out-of-scope feature creep,
- encourage small, testable changes,
- stay aligned with the approved specification and architecture.

## Boundary Guidance

The following boundaries apply:

- extension guidance does not override the source-of-truth documents,
- new contributors should extend interfaces rather than bypassing them,
- plotting and IO remain separate from solver physics during extension work.

## What This Task Does Not Do

This task defines developer extension guidance only. It does not yet:

- define the assumptions and limitations summary,
- implement extension APIs,
- add contributor automation.

Those details belong to later approved tasks.
