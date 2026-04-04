# Thermo Backend Selection Strategy

This document records the approved thermo backend selection strategy for Phase 4 Task `P4-T04`.

## Purpose

The purpose of this strategy is to define how the application selects the correct thermo provider from validated configuration.

Backend selection must remain configuration-driven and must not be hard-coded into solver modules.

## Selection Inputs

Thermo backend selection should be driven by validated configuration inputs, primarily:

- `fluid.working_fluid`
- `models.steam_property_model` when relevant

Future backend-selection fields may be added later without changing solver orchestration.

## MVP Selection Rules

### 1. Air Selection

If `fluid.working_fluid` is `air`:

- select the air thermo provider,
- ignore steam-specific backend selection fields unless later validation rules explicitly allow them.

### 2. Steam Selection

If `fluid.working_fluid` is `steam`:

- select a steam thermo provider through the steam backend selection path,
- use `models.steam_property_model` when provided,
- otherwise use the approved default/standard steam selection behavior once implemented.

### 3. Unsupported Fluid Names

If `fluid.working_fluid` is not supported:

- fail explicitly as a model-selection or configuration error,
- do not silently fall back to another provider.

### 4. Unsupported Steam Backend Names

If a steam backend name is requested but not supported:

- fail explicitly,
- report the unsupported backend name,
- do not silently fall back to another steam provider.

## Future Extensibility Rule

The selection strategy should allow later addition of:

- alternate steam backends,
- additional working fluids,
- backend-specific configuration fields,
without changing the gas solver interface.

## Boundary Guidance

The following boundaries apply:

- selection logic belongs to configuration/application orchestration, not the gas solver,
- solver modules consume the chosen thermo abstraction only,
- concrete providers register behind the selection path,
- output and plotting modules must not participate in provider selection.

## Expected Failure Reporting

Selection failures should report:

- requested working fluid,
- requested backend name when relevant,
- why selection could not proceed,
- whether the issue is unsupported input or unavailable backend support.

## Open Assumptions

The following assumptions apply until later implementation tasks refine behavior:

- air selection is direct and unambiguous in the MVP,
- steam selection may later support multiple backends,
- default steam backend behavior may remain provisional until a concrete backend is chosen,
- registry/factory implementation details are deferred.

## What This Task Does Not Do

This task defines backend selection strategy only. It does not yet:

- implement selection code,
- implement provider registration,
- define default backend constants in code,
- validate steam backend names in code,
- define CLI exposure for backend choices.

Those details belong to later approved tasks.
