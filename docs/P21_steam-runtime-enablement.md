# Phase 21 — Steam Runtime Enablement

## Purpose

Add the first executable steam-provider path behind the existing thermo abstraction, extend backend selection for steam cases, and verify with contract and integration tests — without breaking the air foundation path.

## Implemented Modules

| Module | File | Responsibility |
|---|---|---|
| Steam provider | `thermo/steam.py` | `SteamThermoProvider` — restricted equilibrium-vapor approximation |
| Backend selector | `thermo/selection.py` | Extended `select_thermo_provider()` for steam cases |

## Steam Provider Details

### `SteamThermoProvider` (thermo/steam.py)

- **Model:** Idealized vapor approximation — identical structure to `AirThermoProvider` but with steam-specific constants.
- **Constants:** `R = 461.5 J/(kg·K)`, `γ = 1.33`
- **Properties:** `density = p / (R·T)`, `h = cp·T`, `a = sqrt(γ·R·T)`
- **Range guards:** 1,000–5,000,000 Pa, 300–1,500 K
- **Provider name:** `"equilibrium_steam_mvp"`
- **Working fluid:** `"steam"`

### Design Intent

This provider is a **restricted equilibrium-vapor placeholder** designed for IF97-ready replacement. It uses the same `ThermoProvider` interface, so a future IF97 implementation can be swapped in without changing solver or application code.

### Validity Notes

- Valid only for the MVP equilibrium-steam subset.
- Does not resolve phase-boundary behavior, wet-region properties, or condensation.
- Documented as an IF97-ready placeholder behind the shared thermo interface.

## Backend Selection Extension

Supported steam backend names: `None`, `"equilibrium_mvp"`, `"if97_ready_equilibrium"`

All resolve to `SteamThermoProvider()`. Unsupported backend names raise `ModelSelectionError`.

## YAML Configuration

Steam cases use:
```yaml
fluid:
  working_fluid: steam
models:
  steam_property_model: equilibrium_mvp  # or omit for default
```

## Key Design Decisions

- **Same interface as air** — the gas solver does not know whether it runs with air or steam.
- **IF97-ready architecture** — future IF97 library integration requires only a new concrete provider.
- **Constant-γ simplification** — documented MVP limitation, consistent with the air approach.
- **Air path is preserved** — no changes to `AirThermoProvider` or air selection logic.

## Test Files

- `tests/test_runtime_steam_thermo_provider.py` — valid/invalid state evaluation, range guards, metadata
- `tests/test_runtime_steam_contract_and_integration.py` — interface compliance, selection behavior, gas-only execution with steam

## Tasks Covered

| Task | Title |
|---|---|
| P21-T01 | Implement runtime steam provider for the supported MVP subset |
| P21-T02 | Extend thermo backend selection for supported steam cases |
| P21-T03 | Add steam runtime contract and integration tests |
