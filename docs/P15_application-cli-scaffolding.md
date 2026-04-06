# Phase 15 — Application and CLI Scaffolding

## Purpose

Create the thin application-service and CLI boundaries that coordinate config loading, dependency construction, and later solver orchestration without embedding physics or solver logic in the CLI layer.

## Implemented Modules

| Module | File | Responsibility |
|---|---|---|
| Application service | `app/services.py` | `ApplicationService` dataclass with injected dependencies; `run_startup()` method |
| Public entry points | `app/run_simulation.py` | `get_application_service()`, `run_startup()`, `run_simulation()` |
| CLI entry | `cli/main.py` | `build_parser()`, `parse_cli_args()`, `main()`, `format_startup_report()`, `run_cli()` |
| App package | `app/__init__.py` | Public exports |
| CLI package | `cli/__init__.py` | Public exports |

## Component Details

### `ApplicationService` (app/services.py)

- Frozen dataclass with all dependencies as injectable `Callable` fields.
- `run_startup(case_path)` → `StartupResult`: executes the pre-solver pipeline (load → validate → translate → build geometry → select thermo). Returns structured success/failure.
- Catches `SupersonicAtomizerError`, `FileNotFoundError`, and `ValueError`.

### `StartupResult` / `StartupDependencies`

- `StartupDependencies` bundles `CaseConfig`, `GeometryModel`, `ThermoProvider`.
- `StartupResult` includes status, case path, optional dependencies, and failure context.

### CLI Layer (cli/main.py)

- `CLIOptions` — case path + optional `--startup-only` flag.
- `build_parser()` — argument parser with minimal options.
- `main()` — parses CLI args, delegates to application service.
- `format_startup_report()` — concise user-facing status string.
- `run_cli()` — writes to stdout/stderr and returns exit code.

## Key Design Decisions

- CLI is a thin boundary — no physics, no config parsing, no solver logic.
- All orchestration lives in `ApplicationService` with injected dependencies for testability.
- `run_startup()` returns structured results rather than raising exceptions at the API boundary.
- The app package provides both the injectable service and convenient public entry functions.

## Test Files

- `tests/test_runtime_application_scaffold.py`
- `tests/test_runtime_cli_scaffold.py`

## Tasks Covered

| Task | Title |
|---|---|
| P15-T01 | Create application orchestration scaffold |
| P15-T02 | Implement startup-stage run service flow |
| P15-T03 | Create thin CLI argument parser and entry scaffold |
| P15-T04 | Implement CLI startup reporting behavior |
