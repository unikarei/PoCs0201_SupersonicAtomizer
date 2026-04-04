# Air Thermo Provider Responsibilities

This document records the approved air thermo provider responsibilities for Phase 4 Task `P4-T02`.

## Purpose

The purpose of this document is to define the MVP air-property behavior expected from the concrete air thermo provider.

The air provider must satisfy the shared thermo interface while remaining simple, robust, and appropriate for the MVP.

## MVP Air Modeling Assumptions

For the MVP:

- air may be treated as an ideal gas,
- constant or simply parameterized thermophysical properties are acceptable if documented,
- the provider should support the subset of states needed by approved MVP cases.

## Air Provider Responsibilities

The air thermo provider should:

- identify itself as an air provider,
- evaluate thermodynamic states for supported air queries,
- return SI-unit property values consistent with the thermo interface,
- provide density, sound speed, and enthalpy information needed by the gas solver,
- reject unsupported or nonphysical air states explicitly.

## Supported State Expectations

The MVP air provider should support at least the range of states needed for:

- steady internal quasi-1D compressible flow,
- inlet total condition handling through later solver logic,
- Mach-number evaluation,
- density and temperature-dependent gas-state assembly.

## Expected Property Outputs

The air provider should be able to supply or support construction of:

- pressure,
- temperature,
- density,
- enthalpy,
- sound speed.

Additional derived quantities may be added later if required.

## Error Expectations

The air provider should fail explicitly for conditions such as:

- negative pressure requests,
- nonpositive temperature requests,
- unsupported query combinations,
- returned nonphysical properties.

## Boundary Guidance

The following boundaries apply:

- the air provider must remain behind the thermo interface,
- air-specific formulas must not be embedded directly into unrelated solver modules,
- air behavior must remain separate from steam behavior,
- output and plotting modules must consume solved states rather than query the provider directly.

## Open Assumptions

The following assumptions apply until later implementation tasks refine the provider:

- a simple ideal-gas formulation is sufficient for the MVP,
- exact parameter values and property constants are deferred to implementation,
- advanced real-gas corrections are out of scope for the MVP,
- provider internals should prioritize clarity over model complexity.

## What This Task Does Not Do

This task defines air-provider responsibilities only. It does not yet:

- implement an air provider,
- define exact equations in code,
- define numeric constants,
- define contract tests in detail,
- define solver closure behavior.

Those details belong to later approved tasks.
