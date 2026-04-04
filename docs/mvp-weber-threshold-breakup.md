# MVP Weber-Threshold Breakup Behavior

This document records the approved MVP Weber-threshold breakup behavior for Phase 7 Task `P7-T03`.

## Purpose

The purpose of this document is to specify exactly how breakup is triggered and how droplet diameter metrics change under the approved MVP rule.

## Trigger Logic

For the MVP, breakup is triggered when:

$$
We > We_{crit}
$$

The trigger logic must remain explicit and testable.

## Threshold Handling

The breakup behavior should document and preserve the following threshold expectations:

- if `Weber_number` does not exceed `critical_weber_number`, no breakup is applied,
- if `Weber_number` exceeds `critical_weber_number`, breakup is triggered,
- the comparison rule should remain consistent across all axial locations.

## Diameter-Update Rules

When breakup is triggered, the droplet model should apply prescribed reduction rules to:

- `droplet_mean_diameter`,
- `droplet_maximum_diameter`.

The MVP rule should support configurable factors such as:

- `breakup_factor_mean`,
- `breakup_factor_max`.

## Diameter-Update Expectations

The breakup rule should satisfy all of the following:

- updated diameters remain positive,
- updated maximum diameter should not become smaller than updated mean diameter unless a later approved rule explicitly allows it,
- reduction behavior remains explicit rather than hidden,
- no-breakup states preserve pre-breakup diameters.

## MVP Simplicity Boundary

The MVP breakup behavior does not attempt to resolve:

- breakup mode maps,
- fragment distributions,
- breakup time-scale physics in detail,
- shape-resolved droplet deformation,
- advanced secondary-breakup physics.

## Boundary Guidance

The following boundaries apply:

- the breakup model owns trigger and reduction logic,
- the droplet solver owns transport sequencing,
- the output layer reports breakup results but does not recompute them.

## Open Assumptions

The following assumptions remain open for later approved work:

- whether the same reference diameter is used for all Weber evaluations,
- whether multiple breakup events can occur repeatedly along the grid under the MVP rule,
- whether post-breakup smoothing or limiting is needed in later implementation.

## What This Task Does Not Do

This task defines the MVP Weber-threshold breakup behavior only. It does not yet:

- define registry or selection rules,
- define the droplet-solver integration order in detail,
- define breakup validation cases in detail,
- implement breakup-model code.

Those details belong to later approved tasks.
