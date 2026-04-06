# Phase 18 — Breakup Runtime

## Purpose

Implement the runtime breakup interface, the MVP Weber-threshold breakup model, configuration-driven model selection, and integration into the droplet transport update sequence.

## Implemented Modules

| Module | File | Responsibility |
|---|---|---|
| Interfaces | `breakup/interfaces.py` | `BreakupModel` ABC, `BreakupModelInputs` |
| Weber-critical model | `breakup/weber_critical.py` | `CriticalWeberBreakupModel`, `evaluate_weber_number()` |
| Registry/selector | `breakup/registry.py` | `select_breakup_model()` |
| Diagnostics | `breakup/diagnostics.py` | `validate_breakup_decision()` |

## Breakup Interface

### `BreakupModel` (ABC)

- `model_name` property — stable configuration-facing identifier
- `evaluate(inputs: BreakupModelInputs) → BreakupDecision` — structured local decision

### `BreakupModelInputs`

- `gas_state: GasState` — local gas properties
- `droplet_state: DropletState` — local droplet properties

## Weber Number Evaluation

```python
We = ρ_gas · V_slip² · d / σ
```

- `evaluate_weber_number(gas_density, slip_velocity, reference_diameter, surface_tension)`
- Default surface tension: `σ = 0.072 N/m` (water in air)
- Rejects nonpositive density, diameter, or surface tension

## Critical-Weber Breakup Model

### Trigger Logic

- If `We > We_crit` → breakup triggered
- `d_mean_new = d_mean · breakup_factor_mean`
- `d_max_new = max(d_max · breakup_factor_max, d_mean_new)`

### Parameters (from `ModelSelectionConfig`)

| Parameter | Constraint |
|---|---|
| `critical_weber_number` | > 0 |
| `breakup_factor_mean` | ∈ (0, 1) |
| `breakup_factor_max` | ∈ (0, 1) |

### No-Breakup Path

When `We ≤ We_crit`, diameters are preserved unchanged.

## Model Selection (`select_breakup_model`)

- `"weber_critical"` → `CriticalWeberBreakupModel` (requires explicit breakup factors)
- Other names → `ModelSelectionError`
- Missing factors → `ConfigurationError`

## Breakup Integration in Droplet Transport

In `transport_solver.py`, breakup is applied at each axial step **after** the drag-driven velocity update:

1. Update droplet velocity via drag
2. Call `breakup_model.evaluate()` with current gas/droplet state
3. Replace droplet diameters and Weber number from the `BreakupDecision`
4. Set `breakup_triggered` flag on the resulting `DropletState`

## Diagnostics

`validate_breakup_decision()` checks:
- Finite nonnegative Weber number
- Finite positive critical Weber number
- Finite positive updated diameters
- `max_diameter ≥ mean_diameter`

## Test Files

- `tests/test_runtime_breakup_solver_scaffold.py`
- `tests/test_runtime_breakup_weber_helper.py`
- `tests/test_runtime_weber_critical_breakup_model.py`
- `tests/test_runtime_breakup_selector.py`
- `tests/test_runtime_breakup_integration.py`
- `tests/test_runtime_breakup_diagnostics.py`

## Tasks Covered

| Task | Title |
|---|---|
| P18-T01 | Create breakup runtime module scaffold and selector |
| P18-T02 | Implement runtime Weber number evaluation helper |
| P18-T03 | Implement critical-Weber breakup model runtime path |
| P18-T04 | Integrate breakup execution into droplet transport runtime flow |
| P18-T05 | Implement breakup diagnostics and runtime tests |
