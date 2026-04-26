"""Raw schema-validation scaffold.

This module is reserved for validating the raw external configuration shape.
It must not perform semantic validation, default application, translation, or
solver work.
"""

from __future__ import annotations

from typing import Any


REQUIRED_TOP_LEVEL_SECTIONS = (
    "fluid",
    "boundary_conditions",
    "geometry",
    "droplet_injection",
)

OPTIONAL_TOP_LEVEL_SECTIONS = (
    "case",
    "models",
    "outputs",
)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _require_mapping(parent: dict[str, Any], field_name: str) -> dict[str, Any]:
    value = parent.get(field_name)
    if not isinstance(value, dict):
        raise ValueError(f"Field '{field_name}' must be a mapping.")
    return value


def _require_field(section: dict[str, Any], section_name: str, field_name: str) -> Any:
    if field_name not in section:
        raise ValueError(f"Missing required field '{section_name}.{field_name}'.")
    return section[field_name]


def _require_string(section: dict[str, Any], section_name: str, field_name: str) -> str:
    value = _require_field(section, section_name, field_name)
    if not isinstance(value, str):
        raise ValueError(f"Field '{section_name}.{field_name}' must be a string.")
    return value


def _require_number(section: dict[str, Any], section_name: str, field_name: str) -> float | int:
    value = _require_field(section, section_name, field_name)
    if not _is_number(value):
        raise ValueError(f"Field '{section_name}.{field_name}' must be numeric.")
    return value


def _validate_optional_section_types(raw_config: dict[str, Any]) -> None:
    for section_name in OPTIONAL_TOP_LEVEL_SECTIONS:
        if section_name in raw_config and not isinstance(raw_config[section_name], dict):
            raise ValueError(f"Section '{section_name}' must be a mapping when supplied.")


def _validate_case_section(raw_config: dict[str, Any]) -> None:
    if "case" not in raw_config:
        return

    case_section = _require_mapping(raw_config, "case")
    if "name" in case_section and not isinstance(case_section["name"], str):
        raise ValueError("Field 'case.name' must be a string when supplied.")
    if "description" in case_section and not isinstance(case_section["description"], str):
        raise ValueError("Field 'case.description' must be a string when supplied.")
    if "config_version" in case_section and not isinstance(
        case_section["config_version"],
        (str, int),
    ):
        raise ValueError(
            "Field 'case.config_version' must be a string or integer when supplied."
        )


def _validate_fluid_section(raw_config: dict[str, Any]) -> None:
    fluid_section = _require_mapping(raw_config, "fluid")
    _require_string(fluid_section, "fluid", "working_fluid")
    if "inlet_wetness" in fluid_section and not _is_number(fluid_section["inlet_wetness"]):
        raise ValueError("Field 'fluid.inlet_wetness' must be numeric when supplied.")


def _validate_boundary_conditions(raw_config: dict[str, Any]) -> None:
    bc_section = _require_mapping(raw_config, "boundary_conditions")
    _require_number(bc_section, "boundary_conditions", "Pt_in")
    _require_number(bc_section, "boundary_conditions", "Tt_in")
    _require_number(bc_section, "boundary_conditions", "Ps_out")


def _validate_geometry_section(raw_config: dict[str, Any]) -> None:
    geometry_section = _require_mapping(raw_config, "geometry")
    _require_number(geometry_section, "geometry", "x_start")
    _require_number(geometry_section, "geometry", "x_end")

    n_cells = _require_field(geometry_section, "geometry", "n_cells")
    if not isinstance(n_cells, int) or isinstance(n_cells, bool):
        raise ValueError("Field 'geometry.n_cells' must be an integer.")

    area_distribution = _require_mapping(geometry_section, "area_distribution")
    area_type = _require_string(area_distribution, "geometry.area_distribution", "type")
    if area_type != "table":
        raise ValueError(
            "Field 'geometry.area_distribution.type' must be 'table' in the MVP raw schema."
        )

    x_values = _require_field(area_distribution, "geometry.area_distribution", "x")
    area_values = _require_field(area_distribution, "geometry.area_distribution", "A")
    if not isinstance(x_values, list):
        raise ValueError("Field 'geometry.area_distribution.x' must be an array.")
    if not isinstance(area_values, list):
        raise ValueError("Field 'geometry.area_distribution.A' must be an array.")


def _validate_droplet_injection(raw_config: dict[str, Any]) -> None:
    droplet_section = _require_mapping(raw_config, "droplet_injection")
    _require_number(droplet_section, "droplet_injection", "droplet_velocity_in")
    _require_number(droplet_section, "droplet_injection", "droplet_diameter_mean_in")
    _require_number(droplet_section, "droplet_injection", "droplet_diameter_max_in")
    if "water_mass_flow_rate" in droplet_section and not _is_number(
        droplet_section["water_mass_flow_rate"]
    ):
        raise ValueError(
            "Field 'droplet_injection.water_mass_flow_rate' must be numeric when supplied."
        )


def _validate_models_section(raw_config: dict[str, Any]) -> None:
    if "models" not in raw_config:
        return

    models_section = _require_mapping(raw_config, "models")
    string_fields = (
        "drag_model",
        "breakup_model",
        "steam_property_model",
        "gas_solver_mode",
        "coupling_mode",
        "droplet_distribution_model",
    )
    numeric_fields = (
        "droplet_density",
        "droplet_sphericity",
        "critical_weber_number",
        "breakup_factor_mean",
        "breakup_factor_max",
        "two_way_feedback_relaxation",
        "two_way_convergence_tolerance",
        "droplet_distribution_sigma",
        "khrt_B0",
        "khrt_B1",
        "khrt_Crt",
        "liquid_density",
        "liquid_viscosity",
    )

    for field_name in string_fields:
        if field_name in models_section and not isinstance(models_section[field_name], str):
            raise ValueError(f"Field 'models.{field_name}' must be a string when supplied.")

    for field_name in numeric_fields:
        if field_name in models_section and not _is_number(models_section[field_name]):
            raise ValueError(f"Field 'models.{field_name}' must be numeric when supplied.")

    if "two_way_max_iterations" in models_section:
        value = models_section["two_way_max_iterations"]
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError("Field 'models.two_way_max_iterations' must be an integer when supplied.")


def _validate_outputs_section(raw_config: dict[str, Any]) -> None:
    if "outputs" not in raw_config:
        return

    outputs_section = _require_mapping(raw_config, "outputs")
    if "output_directory" in outputs_section and not isinstance(
        outputs_section["output_directory"],
        str,
    ):
        raise ValueError("Field 'outputs.output_directory' must be a string when supplied.")

    for field_name in ("write_csv", "write_json", "generate_plots"):
        if field_name in outputs_section and not isinstance(outputs_section[field_name], bool):
            raise ValueError(f"Field 'outputs.{field_name}' must be a boolean when supplied.")


def validate_raw_config_schema(raw_config: dict[str, Any]) -> dict[str, Any]:
    """Validate the raw configuration structure against the approved schema.
    """

    if not isinstance(raw_config, dict):
        raise ValueError("Raw configuration must be a mapping.")

    for section_name in REQUIRED_TOP_LEVEL_SECTIONS:
        if section_name not in raw_config:
            raise ValueError(f"Missing required section '{section_name}'.")

    _validate_optional_section_types(raw_config)
    _validate_case_section(raw_config)
    _validate_fluid_section(raw_config)
    _validate_boundary_conditions(raw_config)
    _validate_geometry_section(raw_config)
    _validate_droplet_injection(raw_config)
    _validate_models_section(raw_config)
    _validate_outputs_section(raw_config)

    return raw_config