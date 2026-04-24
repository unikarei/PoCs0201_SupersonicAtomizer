# Appendix C — Laval Nozzle Back-Pressure Sweep and p/p0 Validation

This document accompanies `docs/architecture.md` and describes the CLI-accessible Laval nozzle back-pressure sweep utility and the automated `p/p0` validation report generated from sweep outputs.

Purpose

- Drive a back-pressure sweep of the existing solver for a fixed nozzle geometry.
- Aggregate per-run outputs into a labeled sweep directory.
- Produce an aggregated `p/p0` plot (PNG), a `sweep_summary.json`, and a Markdown validation report describing trend-based pass/warn/fail observations.

Scope and Constraints

- The sweep is implemented at the application-service boundary and must not embed solver logic.
- Outputs are written using the existing IO layer (CSV/JSON writers, plotting helpers).
- Validation checks are qualitative and configurable; they test ordering of `p/p0` curves, regime transitions, and shock-location consistency.

Module Notes

- `app/laval_nozzle_sweep.py`: sweep driver — derives back-pressures, runs cases via the application service, builds aggregated artifacts.
- `cli/main.py` (subcommand): CLI entry `laval-sweep` that delegates to application services.
- `validation/reporting.py`: consumer-level checks for trend-based `p/p0` validations used by the sweep report writer.

Artifacts

- `sweep_<timestamp>/`: directory containing per-run CSV/JSON files and the aggregated `p_p0_plot.png`, `sweep_summary.json`, and `sweep_validation.md`.

Acceptance Criteria (architectural)

- Sweep uses the application service and result models only.
- Report writing is IO-layer-driven; validation logic is in the validation module and returns structured `ValidationReport` objects.
- CLI remains thin and does not implement solver internals.

Usage (example)

```sh
supersonic-atomizer laval-sweep --case examples/air_nozzle.yaml --range 1.0e5:1.0e4:10
```

(See `src/supersonic_atomizer/app/laval_nozzle_sweep.py` for implementation details.)
