# Drag Model Abstraction

This document records the approved drag-model abstraction for Phase 6 Task `P6-T04`.

## Purpose

The purpose of this document is to prevent drag logic from being hard-wired into the droplet solver core and to preserve a clean future extension point.

## Abstraction Role

The drag-model abstraction should provide the droplet solver with a replaceable way to evaluate drag-driven droplet response from local gas and droplet conditions.

## Required Boundary Characteristics

The drag-model boundary should:

- accept structured local gas and droplet inputs,
- accept any required model parameters,
- return structured drag-evaluation results or equivalent transport-ready outputs,
- surface invalid model inputs explicitly.

## MVP Default Model

The MVP default drag model should be a simple spherical drag model.

This default is intentionally limited and should prioritize readability, robustness, and compatibility with representative droplet transport.

## Selection Guidance

The drag model should be selected through configuration or model-selection structures rather than through hard-coded solver branching.

## Extensibility Guidance

The abstraction should allow later addition of:

- alternate drag correlations,
- regime-aware drag variations,
- richer diagnostic outputs.

These future additions should not require rewriting the droplet solver orchestration.

## Boundary Guidance

The following boundaries apply:

- the droplet solver owns transport sequencing,
- the drag model owns drag-correlation details,
- the breakup module remains separate from the drag module,
- output and plotting modules do not perform drag evaluation.

## Validation Guidance

The drag-model abstraction should later support interface-level verification for:

- valid input handling,
- explicit failure behavior,
- deterministic output under fixed conditions,
- compatibility with SI units.

## Open Assumptions

The following assumptions remain open for later approved work:

- exact parameter naming for drag selection,
- the exact shape of drag-result objects,
- whether Reynolds number is part of the drag boundary or a droplet-side derived quantity.

## What This Task Does Not Do

This task defines the drag-model abstraction only. It does not yet:

- define the full update sequence,
- define diagnostics and bounds checks,
- define breakup integration timing,
- implement any drag model code.

Those details belong to later approved tasks.
