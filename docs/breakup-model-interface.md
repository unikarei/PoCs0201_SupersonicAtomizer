# Breakup Model Interface

This document records the approved breakup-model interface for Phase 7 Task `P7-T01`.

## Purpose

The purpose of this document is to create a pluggable boundary between droplet transport and breakup logic.

## Interface Role

The breakup-model interface should provide a replaceable way for the droplet solver to request breakup decisions from local gas and droplet conditions without hard-wiring breakup logic into transport orchestration.

## Required Inputs

The breakup-model boundary should accept structured information that can include at minimum:

- local gas-state context,
- local droplet-state context,
- required model parameters,
- any derived quantities needed by the selected breakup criterion.

## Required Outputs

The breakup-model boundary should return structured information that can include at minimum:

- breakup triggered or not,
- updated mean droplet diameter,
- updated maximum droplet diameter,
- relevant diagnostic values,
- a structured `BreakupDecision` or equivalent result.

## Parameter Requirements

The interface should support model parameters such as:

- critical Weber number,
- mean diameter reduction factor,
- maximum diameter reduction factor,
- any model-selection metadata required by the MVP breakup rule.

## Diagnostic Output Expectations

The breakup-model interface should make relevant diagnostics explicit rather than hiding them in side effects.

Examples include:

- evaluated Weber number,
- threshold comparison result,
- applied reduction factors,
- no-breakup reason or outcome context where useful.

## Boundary Guidance

The following boundaries apply:

- the droplet solver owns transport sequencing,
- the breakup model owns breakup-decision logic,
- the drag model remains separate from the breakup model,
- output and plotting layers do not evaluate breakup physics.

## Extensibility Guidance

The interface should allow later replacement by:

- alternate threshold models,
- richer breakup physics models,
- future mode-aware or time-scale-aware models.

This extensibility must not require rewriting the droplet solver core.

## Open Assumptions

The following assumptions remain open for later approved work:

- the exact shape of the `BreakupDecision` object,
- whether all derived quantities are passed in versus computed inside the breakup model,
- whether later models require additional gas or droplet context.

## What This Task Does Not Do

This task defines the breakup-model interface only. It does not yet:

- define the Weber number contract in detail,
- define the MVP threshold behavior in detail,
- define model selection rules,
- implement breakup-model code.

Those details belong to later approved tasks.
