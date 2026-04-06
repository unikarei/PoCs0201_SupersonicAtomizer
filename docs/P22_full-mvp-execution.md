# Phase 22 — Full MVP Application Execution

## Purpose

Extend the application service and CLI from startup-only to the complete end-to-end simulation workflow: gas solving → droplet transport with breakup → validation → CSV/JSON/plot output → concise CLI reporting. Verify with end-to-end integration tests and ship example cases.

## Implemented Modules

| Module | File | Change |
|---|---|---|
| Application service | `app/services.py` | Added `run_simulation()`, `SimulationRunResult`, full orchestration |
| Public entry points | `app/run_simulation.py` | Added `run_simulation()` public function |
| CLI | `cli/main.py` | Extended `main()` to call `run_simulation()` by default; added `format_run_report()` and `--startup-only` flag |
| Example cases | `examples/air_nozzle.yaml`, `examples/steam_nozzle.yaml` | Annotated reference YAML cases |

## Full Simulation Workflow

`ApplicationService.run_simulation(case_path)`:

```
1. run_startup()          → CaseConfig + GeometryModel + ThermoProvider
2. select_breakup_model() → BreakupModel
3. solve_quasi_1d_gas_flow()   → GasSolution
4. solve_droplet_transport()   → DropletSolution (with breakup)
5. build_output_metadata()     → OutputMetadata
6. ensure_output_directories()
7. assemble_simulation_result() → SimulationResult
8. validate_simulation_result() → ValidationReport
9. write_simulation_result_csv()
10. write_simulation_result_json()
11. generate_profile_plots()
12. Return SimulationRunResult(status="completed")
```

### Error Handling

- **Startup failures** → `SimulationRunResult(status="failed", failure_stage="startup")`
- **Output failures** → `SimulationRunResult(status="output-failed", failure_stage="outputs")` (simulation results preserved)
- **Solver failures** → `SimulationRunResult(status="failed", failure_stage="simulation")`

## CLI Extension

- Default mode: `supersonic-atomizer case.yaml` → runs full simulation
- Startup-only mode: `supersonic-atomizer case.yaml --startup-only` → runs startup only
- `format_run_report()` produces concise status strings:
  - Completed: case path, fluid, validation summary, output directory
  - Output-failed: case path, stage, error message
  - Failed: case path, stage, error message

## Example Cases

### `examples/air_nozzle.yaml`

- Convergent-divergent nozzle with air
- 20 cells, 5-point area table (0.0–1.0 m)
- Inlet: 300 kPa, 500 K; Outlet: 200 kPa
- Droplet: 10 m/s, 100 μm mean, 200 μm max
- Breakup: We_crit = 12, factors = 0.5

### `examples/steam_nozzle.yaml`

- Same geometry as air case
- Steam working fluid with `equilibrium_mvp` backend
- Inlet: 500 kPa, 500 K; Outlet: 300 kPa

## Test Files

- `tests/test_runtime_full_application_service.py` — full service workflow, startup failure, output failure
- `tests/test_runtime_cli_full_run.py` — CLI arg parsing, main routing, format_run_report, run_cli paths
- `tests/test_e2e_air_integration.py` — end-to-end air case (app service, public entry, CLI, missing file)
- `tests/test_e2e_steam_integration.py` — end-to-end steam case (app service, public entry, CLI, settings traceability)

## Key Design Decisions

- **CLI remains thin** — no physics, no solver logic, only reporting.
- **Output failures are distinguished** — simulation results survive `OutputError` (status = `"output-failed"`).
- **Validation runs post-solve** — report is attached to `SimulationResult` before writing.
- **Example cases exercise the full pipeline** — both air and steam paths validated.

## Tasks Covered

| Task | Title |
|---|---|
| P22-T01 | Extend application service to full simulation-run orchestration |
| P22-T02 | Extend CLI from startup-only flow to full run flow |
| P22-T03 | Implement end-to-end air integration workflow test |
| P22-T04 | Implement end-to-end steam-oriented integration workflow test |
| P22-T05 | Reconcile examples and task-plan status with executable MVP behavior |
