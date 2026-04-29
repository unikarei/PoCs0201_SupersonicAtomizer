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
    models_section.setdefault("droplet_density", 998.2)
    models_section.setdefault("droplet_sphericity", 1.0)
    models_section.setdefault("breakup_model", "weber_critical")
    models_section.setdefault("gas_solver_mode", "baseline")
    models_section.setdefault("coupling_mode", "one_way")
    models_section.setdefault("two_way_max_iterations", 3)
    models_section.setdefault("two_way_feedback_relaxation", 0.35)
    models_section.setdefault("two_way_convergence_tolerance", 1.0e-3)
    models_section.setdefault("droplet_distribution_model", "mono")
    models_section.setdefault("droplet_distribution_sigma", 0.35)
    models_section.setdefault(
        "critical_weber_number",
        DEFAULT_CRITICAL_WEBER_NUMBER,
    )
    models_section.setdefault("khrt_B0", 0.61)
    models_section.setdefault("khrt_B1", 40.0)
    models_section.setdefault("khrt_Crt", 0.1)
    models_section.setdefault("liquid_density", 998.2)
    models_section.setdefault("liquid_viscosity", 1.002e-3)
    models_section.setdefault("tab_reduction_fraction", 0.5)
    models_section.setdefault("tab_spring_k", 1.0e-3)
    models_section.setdefault("tab_damping_c", 1.0e-6)
    models_section.setdefault("tab_breakup_threshold", 1.0)

    outputs_section.setdefault("write_csv", True)
    outputs_section.setdefault("write_json", True)
    outputs_section.setdefault("generate_plots", True)
    outputs_section.setdefault("output_directory", "outputs")

    return normalized_config