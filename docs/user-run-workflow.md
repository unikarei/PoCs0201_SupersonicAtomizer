# User Run Workflow Documentation

This document records the approved user run workflow for Phase 10 Task `P10-T03`.

## Purpose

The purpose of this document is to describe the intended CLI-driven usage sequence without exposing implementation details.

## Intended User Workflow

The user-facing workflow should describe the following sequence:

1. prepare a YAML case file,
2. select or confirm the desired output location,
3. run the simulator from the CLI,
4. inspect run status information,
5. locate generated CSV, JSON, and plot artifacts.

## Required Workflow Topics

User documentation should explain at minimum:

- how to provide a YAML case,
- that the simulator runs from a Python CLI workflow,
- where CSV outputs are written,
- where JSON outputs are written,
- where plot artifacts are written,
- how run status and error information are surfaced.

## Documentation Guidance

The user run workflow should satisfy all of the following:

- remain user-facing rather than implementation-facing,
- stay consistent with documented run-artifact conventions,
- keep the workflow short and readable,
- avoid requiring knowledge of internal module boundaries.

## Boundary Guidance

The following boundaries apply:

- user workflow documentation should not embed solver internals,
- user workflow documentation should remain aligned with output and plotting conventions,
- CLI remains the public entry point for the MVP workflow.

## What This Task Does Not Do

This task defines the user run workflow documentation only. It does not yet:

- define developer extension guidance,
- define the assumptions and limitations summary,
- implement the CLI,
- add executable usage commands.

Those details belong to later approved tasks.
