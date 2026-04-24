# Breakup Model Selection


Breakup models are selected in a **configuration-driven** manner via the `ModelSelectionConfig`.

- The registry maps selection keys to concrete breakup implementations.
- Default behavior: the MVP `weber_threshold` model is selected unless overridden in the case YAML.

- The selection strategy is configuration-driven and must explicitly document how unsupported breakup-model names are handled (explicit rejection with actionable errors).

- The selection logic must not fall back silently to defaults; unsupported or misspelled keys must be rejected and the user informed (must not fall back silently).

Common selection keys include `weber_threshold` (Weber-threshold) and may be documented as `Weber-threshold` in user-facing docs.

Include selection keys and expected parameter sets in this document.