# Breakup Model Registry and Selection Strategy

This document records the approved breakup-model registry and selection strategy for Phase 7 Task `P7-T04`.

## Purpose

The purpose of this document is to make breakup-model choice configuration-driven and extensible.

## Selection Role

The application should select the breakup model through validated configuration and model-selection structures rather than hard-coded solver branching.

## MVP Selection Rule

For the MVP, the selected breakup model should default to the approved Weber-threshold breakup model.

## Required Selection Behavior

The selection strategy should support:

- the MVP Weber-threshold model,
- explicit rejection of unsupported breakup-model names,
- a clean extension point for future breakup models.

## Registry Guidance

A registry, factory, or equivalent model-selection boundary should later provide:

- mapping from configured breakup-model name to implementation,
- explicit failure behavior for unknown names,
- stable interface compliance for all registered breakup models.

## Boundary Guidance

The following boundaries apply:

- config owns raw selection fields,
- application orchestration or a registry layer resolves the concrete breakup model,
- the droplet solver consumes the selected breakup-model interface,
- unsupported names must not fall back silently.

## Extensibility Guidance

The selection strategy should allow later addition of:

- alternate threshold models,
- richer breakup formulations,
- experimental or validation-only breakup implementations.

These future models must remain compatible with the common breakup interface.

## Open Assumptions

The following assumptions remain open for later approved work:

- the exact configuration key name used for breakup-model selection,
- whether registry behavior lives in a dedicated module or application service,
- whether model-specific defaults are centralized or attached to model factories.

## What This Task Does Not Do

This task defines breakup-model selection only. It does not yet:

- define the trigger logic itself,
- define the droplet-solver integration order,
- define validation cases,
- implement a registry or factory.

Those details belong to later approved tasks.
