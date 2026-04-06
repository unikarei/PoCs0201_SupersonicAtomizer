# Development Tooling Baseline

This document records the approved development tooling baseline for Phase 1 Task `P1-T03`.

## Purpose

The goal of this baseline is to keep the repository simple, Python-only, and consistent with VS Code workflows while the MVP is being built incrementally.

## Baseline Decisions

### Python Version

- Baseline interpreter target: Python 3.11 or newer.
- Rationale:
  - modern type-hint support,
  - good standard-library coverage,
  - stable support in VS Code Python tooling.

### Environment Management

- Baseline environment tool: `venv`.
- Baseline package installer: `pip`.
- Rationale:
  - Python standard-library support,
  - minimal setup burden,
  - appropriate for an MVP-focused repository.

### Testing

- Baseline test framework: `unittest` from the Python standard library.
- Rationale:
  - no external dependency required for initial repository bootstrap,
  - sufficient for small, incremental tests,
  - compatible with VS Code Python test discovery.

### Linting

- Baseline linter: `ruff`.
- Rationale:
  - fast feedback,
  - broad lint-rule coverage,
  - useful for import hygiene and general code quality.

### Formatting

- Baseline formatter: `black`.
- Rationale:
  - predictable formatting,
  - low bikeshedding overhead,
  - common Python team workflow in VS Code.

### Type Checking Guidance

- Public and non-trivial code should use type hints.
- Static type checking is encouraged and may be formalized in a later task.
- This task does not require a type-checker configuration yet.

## VS Code Alignment

The baseline is chosen to work cleanly with standard VS Code Python development:

- Python interpreter selection through the VS Code Python extension,
- test discovery for `unittest`,
- editor formatting using `black`,
- lint feedback using `ruff`.

## What This Task Does Not Do

This task defines tooling choices only. It does not yet:

- add environment files,
- add formatter or linter configuration files,
- add dependency manifests,
- add editor settings,
- change implementation code.

Those follow-up decisions should be introduced only when required by later approved tasks.
