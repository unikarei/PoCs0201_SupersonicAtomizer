# Droplet Injection Assumptions

This document records the approved droplet injection assumptions for Phase 6 Task `P6-T02`.

## Purpose

The purpose of this document is to make the MVP representation of droplet initial conditions explicit before implementation begins.

## Injection Representation

For the MVP, droplet injection is represented using a single set of representative inlet droplet conditions rather than a full population distribution.

## Required Injection Quantities

The droplet injection design must define handling for:

- injection location,
- initial droplet velocity,
- initial mean droplet diameter,
- initial maximum droplet diameter.

## Injection Location Assumption

For the MVP, the default droplet injection location is the inlet-side start of the axial domain unless a later approved task introduces a more general location model.

This keeps droplet transport aligned with the first gas-state location and avoids premature injection-location complexity.

## Initial Velocity Assumption

The solver must accept an initial droplet velocity in SI units.

Expected handling:

- initialize the first droplet state using the configured inlet droplet velocity,
- preserve explicit separation between gas velocity and droplet velocity,
- allow initial slip to be zero, near zero, or finite.

## Initial Diameter Assumptions

The solver must accept both:

- initial mean droplet diameter,
- initial maximum droplet diameter.

Expected handling:

- both diameters must be positive,
- the maximum diameter should not be smaller than the mean diameter,
- the initial droplet state should preserve both metrics explicitly.

## MVP Simplification Boundaries

The MVP droplet injection model does not attempt to define:

- a full droplet size distribution,
- multiple injection locations,
- time-dependent injection schedules,
- spray-angle or 3D injection geometry,
- droplet temperature evolution.

## Boundary Guidance

The following boundaries apply:

- config validation ensures required injection fields are present and physically meaningful,
- the droplet solver consumes validated injection models rather than raw YAML,
- breakup-related diameter changes occur later during transport and not during injection initialization.

## Open Assumptions

The following assumptions remain open for later approved work:

- whether injected droplet loading metrics become mandatory for all cases,
- whether future cases need off-inlet injection,
- whether later extensions introduce multiple representative droplet classes.

## What This Task Does Not Do

This task defines droplet injection assumptions only. It does not yet:

- define the drag update sequence,
- define Weber-number timing,
- define breakup integration,
- implement injection logic,
- define validation cases.

Those details belong to later approved tasks.
