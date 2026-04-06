# Weber Number Calculation Contract

This document records the approved Weber-number calculation contract for Phase 7 Task `P7-T02`.

## Purpose

The purpose of this document is to standardize the quantity that drives the MVP breakup criterion.

## Definition Role

For the MVP, the Weber number is the explicit breakup-driving quantity used to compare aerodynamic forcing against the configured breakup threshold.

## Required Inputs

The Weber-number contract should define and document the required inputs, which include at minimum:

- local gas density,
- slip velocity,
- representative droplet diameter used by the selected rule,
- liquid surface tension or an equivalent configured property if required by the chosen formulation.

## Units Requirement

The Weber number must be treated as dimensionless.

All input quantities used to compute it must remain in SI units.

## Evaluation Timing

The Weber number should be evaluated at a clearly defined stage within the droplet update flow.

For the MVP planning baseline:

- it must be evaluated using the local gas-droplet state,
- its timing must be explicit relative to slip and drag updates,
- the same timing rule must be used consistently along the axial grid.

## Contract Expectations

The Weber-number contract should satisfy all of the following:

- required inputs are explicit,
- units are explicit,
- the computed value is stored or surfaced for downstream use,
- the quantity is available for diagnostics and output,
- the evaluation remains compatible with the breakup-model interface.

## Boundary Guidance

The following boundaries apply:

- the droplet solver owns the transport sequence,
- the breakup model consumes the breakup-driving quantity according to the defined interface,
- thermo and gas-property evaluation remain outside the breakup contract unless explicitly passed in.

## Open Assumptions

The following assumptions remain open for later approved work:

- which droplet diameter metric is the default reference diameter for the MVP calculation,
- whether Weber number is computed inside the droplet solver or inside the breakup model boundary,
- whether later models require additional dimensionless groups.

## What This Task Does Not Do

This task defines the Weber-number contract only. It does not yet:

- define the full MVP breakup trigger logic,
- define the diameter-reduction rule,
- define model registry behavior,
- implement Weber-number code.

Those details belong to later approved tasks.
