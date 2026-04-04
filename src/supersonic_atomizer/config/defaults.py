"""Configuration default-application scaffold.

This module is reserved for centralized config defaults. It must not perform
solver logic or hide unsupported behavior behind silent fallbacks.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


DEFAULT_CRITICAL_WEBER_NUMBER = 12.0


def _ensure_mapping(
    config: dict[str, Any],
    section_name: str,
) -> dict[str, Any]:
    """Return a mutable mapping section, creating it when omitted."""

    section = config.get(section_name)
    if section is None:
        section = {}
        config[section_name] = section
    return section


def apply_config_defaults(raw_config: dict[str, Any]) -> dict[str, Any]:
    """Populate approved defaults into a semantically valid raw config.

    Defaults are applied only in the config layer and explicit user-provided
    values are preserved.
    """

    normalized_config = deepcopy(raw_config)

    fluid_section = _ensure_mapping(normalized_config, "fluid")
    models_section = _ensure_mapping(normalized_config, "models")
    outputs_section = _ensure_mapping(normalized_config, "outputs")

    fluid_section.setdefault("inlet_wetness", None)

    models_section.setdefault("drag_model", "standard_sphere")
    models_section.setdefault("breakup_model", "weber_critical")
    models_section.setdefault(
        "critical_weber_number",
        DEFAULT_CRITICAL_WEBER_NUMBER,
    )

    outputs_section.setdefault("write_csv", True)
    outputs_section.setdefault("write_json", True)
    outputs_section.setdefault("generate_plots", True)
    outputs_section.setdefault("output_directory", "outputs")

    return normalized_config