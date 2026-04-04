# Gas Boundary-Condition Handling

This document records the approved gas boundary-condition handling guidance for Phase 5 Task `P5-T04`.

## Purpose

The purpose of this document is to specify how inlet total conditions and outlet static pressure are used consistently by the gas solver.

The goal is to make boundary-condition intent explicit before solver implementation begins.

## Required Boundary Inputs

The gas solver boundary-condition design must use:

- inlet total pressure `Pt_in`,
- inlet total temperature `Tt_in`,
- outlet static pressure `Ps_out`.

These remain mandatory gas-side boundary inputs for the MVP.

## Boundary-Condition Roles

### 1. Inlet Total Pressure `Pt_in`

`Pt_in` provides the inlet total-pressure reference for the gas solution.

Expected role:

- contributes to inlet-side thermodynamic state definition,
- participates in the solver’s boundary closure.

### 2. Inlet Total Temperature `Tt_in`

`Tt_in` provides the inlet total-temperature reference for the gas solution.

Expected role:

- contributes to inlet-side thermodynamic state definition,
- participates in energy-consistent gas-state construction.

### 3. Outlet Static Pressure `Ps_out`

`Ps_out` provides the outlet-side static-pressure target or closure reference.

Expected role:

- constrains or closes the axial gas solution,
- defines the downstream pressure condition relevant to the internal flow case.

## Consistency Requirements

Boundary handling should satisfy all of the following:

- inlet total conditions must remain physically meaningful and positive,
- outlet static pressure must remain physically meaningful and positive,
- the selected closure approach must use these quantities consistently,
- invalid or contradictory boundary combinations must fail explicitly.

## Invalid Combination Guidance

The following categories should be treated as invalid or unresolved until later implementation details are defined:

- missing required boundary inputs,
- nonpositive total or static pressures,
- nonpositive inlet total temperature,
- boundary data that leads immediately to nonphysical states,
- combinations that the selected MVP closure cannot support.

## Open Closure Assumptions

The following assumptions remain open for later gas-solver design tasks:

- whether the MVP closure is strictly isentropic,
- whether losses are excluded entirely,
- how choking-aware behavior is handled if required,
- how branch selection is realized when multiple mathematical solutions exist.

These questions must be handled explicitly later rather than hidden in implementation.

## Boundary Guidance

The following boundaries apply:

- config validation ensures boundary fields are present and structurally valid,
- the gas solver owns boundary-condition use within the solver formulation,
- thermo providers supply properties but do not decide global boundary closure,
- output and plotting modules do not participate in boundary-condition resolution.

## What This Task Does Not Do

This task defines boundary-condition handling intent only. It does not yet:

- choose the final closure algorithm,
- define choking logic in detail,
- define branch-selection algorithms,
- implement boundary-condition code,
- define failure criteria in full detail.

Those details belong to later approved tasks.
