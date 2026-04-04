# Steam Thermo Provider Interface Contract

This document records the approved steam thermo provider contract for Phase 4 Task `P4-T03`.

## Purpose

The purpose of this document is to reserve a clean, swappable contract for future IF97-based steam handling while preserving the shared thermo interface used by the gas solver.

## Core Contract Intent

The steam provider must satisfy the same solver-facing thermo contract as other fluids while encapsulating steam-specific property behavior behind the thermo layer.

This contract exists so that future IF97-ready steam support can be added or replaced without changing solver orchestration.

## Steam Provider Responsibilities

The steam thermo provider should:

- identify itself as a steam provider,
- satisfy the shared thermo-provider interface,
- evaluate supported steam states for approved MVP cases,
- return SI-unit property values,
- surface validity limits and unsupported state requests explicitly.

## Equilibrium Assumption

For the first release:

- steam behavior should assume equilibrium steam,
- the provider may support only the subset of states needed by approved MVP cases,
- non-equilibrium steam behavior is out of scope.

## Expected State Query Support

The steam provider should be designed to support state queries needed by the quasi-1D gas solver, including those required to obtain:

- pressure,
- temperature,
- density,
- enthalpy,
- sound speed.

Exact supported independent-variable combinations may depend on the future backend, but the solver-facing contract must remain stable.

## Validity Constraints

The steam provider contract should document and later enforce constraints such as:

- supported thermodynamic region subset for the MVP,
- rejection of out-of-range state requests,
- explicit handling of unsupported phase-region requests,
- explicit handling of unavailable backend capabilities.

## IF97 Readiness Requirement

The steam contract must be designed so that an IF97-based backend can later be used cleanly.

That means:

- solver code must not depend on steam-specific implementation details,
- backend selection must remain configuration-driven,
- concrete library choice must remain replaceable.

## Boundary Guidance

The following boundaries apply:

- steam logic must remain isolated inside the thermo layer,
- steam-specific property handling must not leak into unrelated modules,
- the gas solver must consume the shared thermo abstraction rather than a steam-specific API,
- plotting and IO must not access steam backends directly.

## Open Assumptions

The following assumptions apply until later implementation tasks refine the provider:

- the initial executable MVP may support only a restricted steam subset,
- IF97 backend choice remains open,
- optional wetness handling may be constrained by the supported state region,
- advanced wet-steam or non-equilibrium behavior is deferred.

## What This Task Does Not Do

This task defines the steam provider contract only. It does not yet:

- choose a concrete IF97 library,
- implement a steam provider,
- define backend-specific equations,
- define exact supported phase regions in code,
- define contract tests in detail.

Those details belong to later approved tasks.
