# Phase 11 — Runtime Config Foundations

## Purpose

Establish the runtime configuration pipeline that loads a YAML case file, validates its structure and semantics, applies centralized defaults, and translates the result into typed internal models consumed by all downstream layers.

## Implemented Modules

| Module | File | Responsibility |
|---|---|---|
| Config package | `src/supersonic_atomizer/config/__init__.py` | Public exports for loader, defaults, schema, semantics, translator |
| YAML loader | `config/loader.py` | Read and parse one YAML case file into a raw `dict` |
| Schema validator | `config/schema.py` | Enforce required top-level sections, field types, and MVP constraints |
| Semantic validator | `config/semantics.py` | Reject nonphysical values (negative pressures, inconsistent geometry, etc.) |
| Defaults applier | `config/defaults.py` | Centralize approved runtime defaults (drag model, breakup model, Weber threshold, output flags) |
| Config translator | `config/translator.py` | Translate validated raw config into typed `CaseConfig` and sub-models |

## Processing Pipeline

```
YAML file
  → load_raw_case_config      (loader.py)
  → validate_raw_config_schema (schema.py)
  → validate_semantic_config   (semantics.py)
  → apply_config_defaults      (defaults.py)
  → translate_case_config      (translator.py)
  → CaseConfig                 (domain/case_models.py)
```

## Key Design Decisions

- **YAML structure never leaks downstream.** Only the config layer touches raw `dict` structures; all other layers receive typed dataclasses.
- **Defaults are centralized in one module** (`defaults.py`) rather than scattered across solvers.
- **Schema and semantic validation are separate stages** so structural errors are caught before physical-value checks.
- **Errors use explicit categories:** `FileNotFoundError` / `ValueError` for parse problems; downstream layers convert to `ConfigurationError` or `InputParsingError`.

## Centralized Defaults

| Parameter | Default Value |
|---|---|
| `drag_model` | `"standard_sphere"` |
| `breakup_model` | `"weber_critical"` |
| `critical_weber_number` | `12.0` |
| `write_csv` | `True` |
| `write_json` | `True` |
| `generate_plots` | `True` |
| `output_directory` | `"outputs"` |

## Test Files

- `tests/test_yaml_case_loader.py` — valid/invalid YAML loading
- `tests/test_raw_config_schema_validation.py` — required sections and field checks
- `tests/test_semantic_config_validation_runtime.py` — nonphysical value rejection
- `tests/test_config_defaults_application_runtime.py` — default merging behavior
- `tests/test_config_translation_runtime.py` — end-to-end raw-to-model translation
- `tests/test_runtime_config_module_scaffold.py` — import and wiring verification

## Tasks Covered

| Task | Title |
|---|---|
| P11-T01 | Create runtime config module scaffold |
| P11-T02 | Implement YAML case loader |
| P11-T03 | Implement config defaults application |
| P11-T04 | Implement raw schema validation |
| P11-T05 | Implement semantic config validation |
| P11-T06 | Implement config translation to internal runtime models |
