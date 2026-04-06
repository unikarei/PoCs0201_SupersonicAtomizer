# Phase 12 — Runtime Domain Models

## Purpose

Define the typed internal data models used across all runtime layers — case configuration, solver states, simulation results, diagnostics, and categorized error classes.

## Implemented Modules

| Module | File | Responsibility |
|---|---|---|
| Case config models | `domain/case_models.py` | `CaseConfig`, `FluidConfig`, `BoundaryConditionConfig`, `GeometryConfig`, `DropletInjectionConfig`, `ModelSelectionConfig`, `OutputConfig` |
| Solver state models | `domain/state_models.py` | `ThermoState`, `GasState`, `GasSolution`, `DropletState`, `DropletSolution`, `BreakupDecision` |
| Result/diagnostics models | `domain/result_models.py` | `SimulationResult`, `RunDiagnostics`, `ValidationReport`, `OutputMetadata` |
| Error classes | `common/errors.py` | `SupersonicAtomizerError` hierarchy |

## Model Inventory

### Case Configuration (`case_models.py`)

All frozen `@dataclass` with `slots=True`:

- `FluidConfig` — working fluid name and optional inlet wetness
- `BoundaryConditionConfig` — `Pt_in`, `Tt_in`, `Ps_out` (SI)
- `GeometryConfig` — axial range, cell count, area definition dict
- `DropletInjectionConfig` — initial velocity, mean/max diameters, optional mass flow rate
- `ModelSelectionConfig` — drag model, breakup model, critical Weber, breakup factors, steam backend
- `OutputConfig` — output directory, CSV/JSON/plot flags
- `CaseConfig` — top-level aggregate with optional case name/description/version

### Solver States (`state_models.py`)

- `ThermoState` — pressure, temperature, density, enthalpy, sound speed
- `GasState` — local axial gas state including area and Mach number
- `GasSolution` — full axial history with `__post_init__` length validation
- `DropletState` — velocity, slip, diameters, Weber, Reynolds, breakup flag
- `DropletSolution` — full axial history with `__post_init__` length validation
- `BreakupDecision` — triggered flag, Weber values, updated diameters, reason string

### Results and Diagnostics (`result_models.py`)

- `RunDiagnostics` — status, warnings, messages, failure context
- `ValidationReport` — check counts, observations, overall status
- `OutputMetadata` — run ID, directory paths, CSV/JSON/plot paths, flags
- `SimulationResult` — top-level aggregate consumed by IO, plotting, and validation

### Error Taxonomy (`common/errors.py`)

```
SupersonicAtomizerError
  ├─ InputParsingError
  ├─ ConfigurationError
  ├─ ModelSelectionError
  ├─ ThermoError
  ├─ NumericalError
  ├─ OutputError
  └─ ValidationError
```

## Key Design Decisions

- All models are frozen dataclasses — immutable after construction.
- `GasSolution` and `DropletSolution` use `__post_init__` to enforce array-length consistency.
- Error classes carry no solver logic; they exist purely for categorization.
- Models are free of YAML parsing, plotting, and file serialization.

## Test Files

- `tests/test_runtime_case_configuration_models.py`
- `tests/test_runtime_solver_state_models.py`
- `tests/test_runtime_result_and_diagnostics_models.py`
- `tests/test_runtime_error_classes.py`

## Tasks Covered

| Task | Title |
|---|---|
| P12-T01 | Implement runtime case-configuration models |
| P12-T02 | Implement runtime solver-state models |
| P12-T03 | Implement runtime result and diagnostics models |
| P12-T04 | Implement runtime error classes |
