# Thermo Provider Interface

This document records the approved thermo provider interface for Phase 4 Task `P4-T01`.

## Purpose

The purpose of the thermo provider interface is to define the boundary the gas solver uses for all fluid-property access.

The interface must allow the gas solver to depend on abstract thermodynamic behavior rather than on concrete `air` or `steam` implementations.

## Core Interface Concept

The thermo layer should later expose a provider abstraction conceptually equivalent to `ThermoProvider`.

### Role

`ThermoProvider` should:

- evaluate thermodynamic state from supported input variables,
- return consistent property data in SI units,
- expose provider metadata and validity limits,
- surface thermo-specific failures explicitly.

## Required Operations

The interface should support at least the following conceptual operations.

### 1. State Evaluation

Recommended capability:

- evaluate a thermodynamic state from supported independent variables

Expected use:

- construct a `ThermoState` for gas-solver use,
- support the subset of state queries needed by the MVP gas solver.

### 2. Density Access

Recommended capability:

- provide density as part of thermo-state evaluation or as a directly queryable property

### 3. Sound Speed Access

Recommended capability:

- provide sound speed needed for Mach-number evaluation

### 4. Enthalpy or Equivalent Energy Property

Recommended capability:

- provide enthalpy or another approved energy-consistent property needed by solver formulations

### 5. Metadata Access

Recommended capability:

- expose provider name,
- expose working fluid,
- expose supported state domain or validity notes

## Expected Inputs

Supported thermo queries may later use combinations such as:

- pressure and temperature,
- total conditions with additional closure inputs,
- other approved independent variables required by the selected solver formulation.

The exact state-query combinations may vary by provider implementation, but the solver-facing interface must remain consistent in intent.

## Expected Outputs

The interface should return or support construction of a `ThermoState` containing at least:

- `pressure`
- `temperature`
- `density`
- `enthalpy`
- `sound_speed`

## SI Unit Requirements

All thermo-provider inputs and outputs must use SI units.

Examples:

- pressure in Pa,
- temperature in K,
- density in kg/m^3,
- enthalpy in J/kg,
- sound speed in m/s.

## Error Conditions

The thermo interface must surface explicit thermo-related failures for conditions such as:

- invalid state requests,
- out-of-range queries,
- unsupported phase-region requests,
- unavailable backend functionality,
- nonphysical returned property values.

## Boundary Guidance

The following architectural boundaries apply:

- gas-solver code must depend on the thermo interface rather than direct fluid-property formulas where practical,
- concrete `air` and `steam` providers must remain separate from the gas solver core,
- configuration selects providers, but solver code consumes the abstract thermo contract,
- plotting and IO must not access raw thermo backends directly.

## Open Assumptions

The following assumptions apply until later thermo tasks refine the details:

- the MVP solver needs only a limited subset of thermo operations,
- the interface should be future-ready for IF97-based steam support,
- exact Python method names are deferred to later implementation,
- provider-specific optimizations are out of scope for this task.

## What This Task Does Not Do

This task defines the thermo provider interface only. It does not yet:

- implement Python interfaces or abstract base classes,
- define concrete air behavior,
- define concrete steam behavior,
- define backend selection code,
- define contract tests in detail.

Those details belong to later approved tasks.
