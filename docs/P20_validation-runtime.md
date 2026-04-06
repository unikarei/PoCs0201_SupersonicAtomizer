# Phase 20 — Validation Runtime

## Purpose

Execute structured post-solve validation checks against simulation results, assemble validation reports, and propagate validation failures through the approved error categories — all without coupling to solver internals.

## Implemented Modules

| Module | File | Responsibility |
|---|---|---|
| Sanity checks | `validation/sanity_checks.py` | `run_sanity_checks()` and individual check functions |
| Reporting | `validation/reporting.py` | `ValidationCheckResult`, `assemble_validation_report()`, `validate_simulation_result()` |

## Validation Checks

### Prerequisite Checks (Always Run)

- **Axial alignment** — gas and droplet solution lengths must match, x-coordinates must be identical.
- **Finiteness** — Weber number series must be finite.

### Check Functions

| Check | Condition | Expected Behavior |
|---|---|---|
| `_check_gas_solution_completion` | Always | Verifies gas arrays are finite and diagnostics status is `"completed"` |
| `_check_zero_or_near_zero_slip_case` | Initial slip ≤ 1e-9 | Slip should remain ≤ 1e-6 throughout (no spurious acceleration) |
| `_check_slip_driven_acceleration_case` | Initial slip > 1e-9 | Droplet velocity should increase, slip should decrease |
| `_check_breakup_behavior` | Always | No-trigger: diameters preserved. Trigger: diameters decrease, max ≥ mean |

### Check Results

Each check returns a `ValidationCheckResult` with:
- `name` — machine-readable identifier
- `status` — `"pass"`, `"warn"`, or `"fail"`
- `observation` — human-readable trend description

## Report Assembly

`assemble_validation_report(check_results)` → `ValidationReport`:
- Counts checks run, passed, warned, failed
- Overall status: `"fail"` if any failed, `"warn"` if any warned, else `"pass"`
- Observations tuple from all individual checks

## Public Entry Point

`validate_simulation_result(simulation_result)` — convenience function that runs all checks and returns the assembled report.

## Error Handling

- Validation execution failures raise `ValidationError` (from `common/errors.py`).
- Validation check failures (pass/warn/fail outcomes) are **not** exceptions — they are data in the `ValidationReport`.
- `raise_validation_failure()` helper for structural validation problems (e.g., misaligned inputs).

## Key Design Decisions

- **Validation consumes `SimulationResult` only** — no solver internals, no raw config, no YAML.
- **Checks are conditional** — slip-driven and zero-slip checks only run when applicable.
- **Validation is distinct from testing** — checks physical trends and expectations, not software correctness.
- **Structured reports** enable downstream CLI reporting and future dashboard integration.

## Test Files

- `tests/test_runtime_validation_scaffold.py`
- `tests/test_runtime_validation_sanity_checks.py`
- `tests/test_runtime_validation_reporting.py`
- `tests/test_runtime_validation_failures.py`

## Tasks Covered

| Task | Title |
|---|---|
| P20-T01 | Create validation runtime module scaffold |
| P20-T02 | Implement runtime sanity-check execution path |
| P20-T03 | Implement validation-report assembly runtime path |
| P20-T04 | Implement validation failure propagation behavior |
