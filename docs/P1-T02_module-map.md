# Module Map

This document records the package naming decision and module boundaries defined for Phase 1 Task `P1-T02`.

## Package Name

The repository uses the Python package name `supersonic_atomizer`.

## Module Groups

- `supersonic_atomizer.app`
  - application orchestration and end-to-end workflow coordination
- `supersonic_atomizer.cli`
  - command-line entry points and argument handling
- `supersonic_atomizer.config`
  - YAML loading, schema validation, defaults, and translation into internal models
- `supersonic_atomizer.domain`
  - shared case, state, result, and diagnostics data models
- `supersonic_atomizer.thermo`
  - thermodynamic interfaces and fluid-property providers
- `supersonic_atomizer.geometry`
  - area-profile and geometry representation
- `supersonic_atomizer.grid`
  - axial grid representation and grid generation support
- `supersonic_atomizer.solvers.gas`
  - quasi-1D gas-flow solver components
- `supersonic_atomizer.solvers.droplet`
  - droplet transport solver components
- `supersonic_atomizer.breakup`
  - pluggable breakup-model interfaces and implementations
- `supersonic_atomizer.io`
  - CSV/JSON writers and output-path helpers
- `supersonic_atomizer.plotting`
  - Matplotlib plotting isolated from solver logic
- `supersonic_atomizer.validation`
  - sanity checks, validation cases, and reporting
- `supersonic_atomizer.common`
  - shared constants, unit helpers, and error definitions used across modules

## Boundary Notes

- `config` must not contain solver logic.
- `domain` defines data contracts and must stay free of file IO and solver algorithms.
- `thermo` remains the abstraction boundary for air and future IF97-ready steam support.
- `solvers` consume typed models and abstract interfaces rather than raw YAML.
- `breakup` remains configuration-selectable and solver-independent.
- `io` and `plotting` consume structured results only and must not recompute physics.
- `validation` remains separate from production solver logic.

## Scope of This Task

This task defines names and boundaries only. It does not implement solver behavior, schema parsing, thermo calculations, or CLI commands.
