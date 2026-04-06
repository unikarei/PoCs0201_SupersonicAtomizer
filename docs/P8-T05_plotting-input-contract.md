# Plotting Input Contract

This document records the approved plotting input contract for Phase 8 Task `P8-T05`.

## Purpose

The purpose of this document is to keep plotting independent of solver internals.

## Contract Role

The plotting layer should consume only structured result objects and output settings.

## Required Plotting Inputs

The plotting contract should accept at minimum:

- structured simulation result data,
- output or plotting settings,
- file/directory targets needed for plot artifact generation.

## Required Result Content

The structured result input should provide access to:

- axial coordinate data,
- the gas variables required by the MVP plot set,
- the droplet variables required by the MVP plot set,
- breakup-related indicators where available,
- metadata useful for figure labeling where appropriate.

## Contract Requirements

The plotting contract should satisfy all of the following:

- it does not depend on raw solver internals,
- it does not parse raw YAML,
- it does not recompute physics,
- it can operate from stable result-model fields alone,
- it remains reusable across result-writing and validation workflows.

## Boundary Guidance

The following boundaries apply:

- result assembly owns the final structured result,
- plotting owns figure generation only,
- solver layers do not own plotting behavior,
- IO and plotting remain separate concerns even when they share output settings.

## Open Assumptions

The following assumptions remain open for later approved work:

- the exact shape of plotting settings,
- whether plotting accepts a combined result object or a narrower plotting-view model,
- how styling configuration is layered over the plotting contract.

## What This Task Does Not Do

This task defines the plotting input contract only. It does not yet:

- define plot-generation failure behavior,
- define exact style settings,
- define output file naming in full detail,
- implement plotting code.

Those details belong to later approved tasks.
