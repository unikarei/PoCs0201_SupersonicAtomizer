# Phase 14 — Thermo Runtime Foundations

## Purpose

Establish the runtime thermodynamic abstraction layer: a provider interface, the first concrete air implementation, configuration-driven backend selection, and structured failure propagation.

## Implemented Modules

| Module | File | Responsibility |
|---|---|---|
| Provider interface | `thermo/interfaces.py` | `ThermoProvider` ABC and `ThermoProviderMetadata` |
| Air provider | `thermo/air.py` | `AirThermoProvider` — ideal gas with constant γ |
| Backend selector | `thermo/selection.py` | `select_thermo_provider()` from `CaseConfig` |
| Failure helpers | `thermo/failures.py` | `evaluate_thermo_state()` wrapping evaluation errors |

## Component Details

### `ThermoProvider` (thermo/interfaces.py)

Abstract base class requiring:

- `metadata` property → `ThermoProviderMetadata` (name, fluid, validity notes)
- `evaluate_state(pressure, temperature)` → `ThermoState`
- Convenience properties: `provider_name`, `working_fluid`, `validity_notes`

### `AirThermoProvider` (thermo/air.py)

- Ideal-gas model: `R = 287.05 J/(kg·K)`, `γ = 1.4`.
- `density = p / (R·T)`, `h = cp·T`, `a = sqrt(γ·R·T)`.
- Input range guards: 100–10,000,000 Pa, 150–2,000 K.
- Raises `ThermoError` for invalid/out-of-range states.

### `select_thermo_provider()` (thermo/selection.py)

- `"air"` → `AirThermoProvider()`
- `"steam"` → `SteamThermoProvider()` (requires supported backend name or `None`)
- Unsupported fluid or backend → `ModelSelectionError`

### `evaluate_thermo_state()` (thermo/failures.py)

- Wraps arbitrary provider evaluation.
- Preserves `ThermoError` pass-through; wraps unexpected exceptions into `ThermoError`.

## Key Design Decisions

- Gas solver depends on `ThermoProvider` abstraction, never on `AirThermoProvider` directly.
- Air uses constant properties — documented as MVP simplification.
- Range validation is provider-side, not solver-side.
- Failure propagation preserves the `ThermoError` category throughout.

## Test Files

- `tests/test_runtime_thermo_provider_interface.py`
- `tests/test_runtime_air_thermo_provider.py`
- `tests/test_runtime_thermo_backend_selection.py`
- `tests/test_runtime_thermo_failure_propagation.py`

## Tasks Covered

| Task | Title |
|---|---|
| P14-T01 | Implement runtime thermo provider interface |
| P14-T02 | Implement runtime air thermo provider |
| P14-T03 | Implement thermo backend selection for supported foundation cases |
| P14-T04 | Implement thermo failure propagation rules |
