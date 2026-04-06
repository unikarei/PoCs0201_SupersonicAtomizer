# Solver State Models

This document records the approved solver state models for Phase 2 Task `P2-T04`.

## Purpose

The purpose of these models is to define the internal representation of thermo state, gas state, droplet state, and breakup decisions used across solver layers.

These models are solver-facing internal contracts. They are distinct from raw YAML configuration models and from final output/result models.

## Model Set Overview

The solver-state layer should define the following internal models:

- `ThermoState`
- `GasState`
- `GasSolution`
- `DropletState`
- `DropletSolution`
- `BreakupDecision`

## 1. `ThermoState`

Thermodynamic state at a single thermodynamic evaluation point.

### Role

`ThermoState` represents thermodynamic properties returned by a fluid-property provider.

### Expected Fields

- `pressure`
- `temperature`
- `density`
- `enthalpy`
- `sound_speed`

### Notes

- Additional properties may be added later if required by a provider interface.
- Values are expected to remain in SI units.
- This model should remain independent of solver marching logic.

## 2. `GasState`

Gas-flow state at one axial location.

### Role

`GasState` represents the local quasi-1D gas solution at a single axial point.

### Expected Fields

- `x`
- `area`
- `pressure`
- `temperature`
- `density`
- `velocity`
- `mach_number`
- `thermo_state`

### Notes

- `thermo_state` may be embedded or otherwise associated to preserve a clean connection to thermo evaluation.
- This model should represent a local state only, not the full domain history.

## 3. `GasSolution`

Full gas-solver result across the axial grid.

### Role

`GasSolution` represents the ordered axial history of gas states together with gas-solver diagnostics.

### Expected Fields

- `states`
- `x_values`
- `area_values`
- `pressure_values`
- `temperature_values`
- `density_values`
- `velocity_values`
- `mach_number_values`
- `diagnostics`

### Notes

- `states` should preserve ordered local `GasState` instances or their equivalent.
- Array-style fields support downstream plotting and output generation.
- Diagnostics should remain separate from raw numeric arrays when practical.

## 4. `DropletState`

Droplet state at one axial location.

### Role

`DropletState` represents the local representative-droplet solution at a single axial point.

### Expected Fields

- `x`
- `velocity`
- `slip_velocity`
- `mean_diameter`
- `maximum_diameter`
- `weber_number`
- `reynolds_number`
- `breakup_triggered`

### Notes

- `reynolds_number` may remain optional when not yet evaluated.
- `breakup_triggered` should capture local breakup status without encoding broader history.
- This model should describe local droplet state only.

## 5. `DropletSolution`

Full droplet-solver result across the axial grid.

### Role

`DropletSolution` represents the ordered axial history of droplet states and breakup-related indicators.

### Expected Fields

- `states`
- `x_values`
- `velocity_values`
- `slip_velocity_values`
- `mean_diameter_values`
- `maximum_diameter_values`
- `weber_number_values`
- `reynolds_number_values`
- `breakup_flags`
- `diagnostics`

### Notes

- `states` should preserve ordered local `DropletState` instances or their equivalent.
- Array-style fields support result assembly, export, and plotting.
- Diagnostics should record warnings or anomalies separately from physical state values.

## 6. `BreakupDecision`

Structured breakup decision for a local droplet update.

### Role

`BreakupDecision` represents the outcome of a breakup-model evaluation at one update point.

### Expected Fields

- `triggered`
- `weber_number`
- `critical_weber_number`
- `updated_mean_diameter`
- `updated_maximum_diameter`
- `reason`

### Notes

- `triggered` should be explicit rather than inferred indirectly.
- The decision should carry enough information for solver updates and diagnostics.
- This model should avoid hidden side effects and should remain independent of plotting/output concerns.

## Boundary Guidance

The following boundary rules apply to these models:

- solver state models must not contain raw YAML parsing logic,
- solver state models must not contain plotting or file-serialization logic,
- solver state models should be easy to inspect and test,
- local state models and full-solution models should remain distinct,
- breakup decisions should remain separate from droplet transport state updates.

## Relationship to Other Model Groups

These solver state models are distinct from:

- case configuration models,
- geometry/grid definition models,
- final result and diagnostics models,
- error model taxonomy.

Those model groups are handled in separate tasks.

## What This Task Does Not Do

This task defines solver state model structure only. It does not yet:

- implement Python dataclasses or typed classes,
- define result aggregation models,
- define diagnostics structures in detail,
- define solver algorithms,
- define breakup registry behavior.

Those details belong to later approved tasks.
