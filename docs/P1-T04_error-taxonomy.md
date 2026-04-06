# Error Category Taxonomy

This document records the approved application-level error taxonomy for Phase 1 Task `P1-T04`.

## Purpose

The purpose of this taxonomy is to define clear, stable error categories before implementation spreads error handling across configuration, thermo, solver, IO, and validation modules.

The taxonomy is intended to support:

- clearer diagnostics,
- consistent exception design later,
- cleaner CLI error reporting,
- separation between user-input errors and numerical/model failures.

## Core Error Categories

### 1. Input Parsing Errors

Use for failures while reading external input sources before semantic interpretation.

Examples:

- missing YAML file,
- unreadable file path,
- invalid YAML syntax,
- malformed external file contents.

### 2. Configuration Errors

Use for structurally valid input that fails repository-defined configuration requirements.

Examples:

- missing required fields,
- unsupported field combinations,
- invalid boundary-condition combinations,
- invalid geometry or droplet configuration after parsing.

### 3. Model-Selection Errors

Use when a requested configurable model or backend name is unsupported or unavailable.

Examples:

- unsupported working fluid,
- unknown breakup model name,
- unavailable thermo backend,
- unsupported drag-model selector.

### 4. Thermo Errors

Use for failures originating inside thermodynamic-property evaluation or thermo-backend validity checks.

Examples:

- invalid thermo state request,
- out-of-range steam property query,
- unsupported phase-region request,
- backend-specific property-evaluation failure.

### 5. Numerical Errors

Use for failures during solver execution, state update, or numerical closure.

Examples:

- nonphysical state encountered,
- failed solver closure,
- branch ambiguity,
- NaN or infinite state values,
- incomplete axial solution progression.

### 6. Output Errors

Use for failures while writing result artifacts or organizing output paths.

Examples:

- CSV write failure,
- JSON serialization failure,
- invalid output directory,
- plot file write failure.

### 7. Validation Errors

Use for failures in validation execution or validation-report generation.

Examples:

- invalid validation-case definition,
- failed validation artifact loading,
- inconsistent validation metadata,
- validation reporting failure.

## Severity Guidance

The architecture should later distinguish between:

- fatal errors,
- recoverable warnings,
- informational diagnostics.

This taxonomy defines categories, not severity by itself.

## Boundary Guidance

- Parsing and configuration errors should be raised as early as possible.
- Model-selection and thermo errors should remain separate from generic numerical failures.
- Output and validation errors should not be misreported as solver failures.
- CLI reporting should summarize the category clearly for users.

## What This Task Does Not Do

This task defines category names and intended usage only. It does not yet:

- implement exception classes,
- define exact class inheritance,
- define logging format,
- define warning object models,
- implement category-to-exit-code mapping.

Those details should be introduced only when required by later approved tasks.
