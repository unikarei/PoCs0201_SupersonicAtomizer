"""Semantic-validation scaffold.

This module is reserved for runtime semantic validation of already structured
configuration data. It must remain separate from raw schema checks, default
application, translation, and solver work.
"""

from __future__ import annotations

from typing import Any


def _require_positive(value: Any, field_name: str) -> None:
    if value <= 0:
        raise ValueError(f"Field '{field_name}' must be positive.")


def _validate_boundary_conditions(raw_config: dict[str, Any]) -> None:
    boundary_conditions = raw_config["boundary_conditions"]
    _require_positive(boundary_conditions["Pt_in"], "boundary_conditions.Pt_in")
    _require_positive(boundary_conditions["Tt_in"], "boundary_conditions.Tt_in")
    _require_positive(boundary_conditions["Ps_out"], "boundary_conditions.Ps_out")


def _validate_geometry(raw_config: dict[str, Any]) -> None:
    geometry = raw_config["geometry"]
    x_start = geometry["x_start"]
    x_end = geometry["x_end"]
    n_cells = geometry["n_cells"]

    if x_end <= x_start:
        raise ValueError("Field 'geometry.x_end' must be greater than 'geometry.x_start'.")
    if n_cells <= 0:
        raise ValueError("Field 'geometry.n_cells' must be greater than zero.")

    area_distribution = geometry["area_distribution"]
    if area_distribution["type"] != "table":
        raise ValueError(
            "Field 'geometry.area_distribution.type' must be 'table' for the MVP."
        )

    x_values = area_distribution["x"]
    area_values = area_distribution["A"]

    if len(x_values) != len(area_values):
        raise ValueError(
            "Fields 'geometry.area_distribution.x' and 'geometry.area_distribution.A' must have the same length."
        )
    if len(x_values) == 0:
        raise ValueError("Area table arrays must be non-empty.")
    if len(x_values) < 2:
        raise ValueError("Area table must contain at least two points.")

    for area_value in area_values:
        _require_positive(area_value, "geometry.area_distribution.A")

    for index in range(1, len(x_values)):
        if x_values[index] <= x_values[index - 1]:
            raise ValueError(
                "Field 'geometry.area_distribution.x' must be strictly increasing."
            )

    if x_values[0] != x_start or x_values[-1] != x_end:
        raise ValueError(
            "Area table endpoints must match 'geometry.x_start' and 'geometry.x_end'."
        )


def _validate_fluid_section(raw_config: dict[str, Any]) -> None:
    fluid = raw_config["fluid"]
    working_fluid = fluid["working_fluid"]

    if working_fluid not in {"air", "steam"}:
        raise ValueError("Field 'fluid.working_fluid' must be 'air' or 'steam'.")

    inlet_wetness = fluid.get("inlet_wetness")
    if working_fluid == "air" and inlet_wetness is not None:
        raise ValueError(
            "Field 'fluid.inlet_wetness' is unsupported for air cases when set."
        )


def _validate_droplet_injection(raw_config: dict[str, Any]) -> None:
    droplet_injection = raw_config["droplet_injection"]
    _require_positive(
        droplet_injection["droplet_diameter_mean_in"],
        "droplet_injection.droplet_diameter_mean_in",
    )
    _require_positive(
        droplet_injection["droplet_diameter_max_in"],
        "droplet_injection.droplet_diameter_max_in",
    )

    if (
        droplet_injection["droplet_diameter_max_in"]
        < droplet_injection["droplet_diameter_mean_in"]
    ):
        raise ValueError(
            "Field 'droplet_injection.droplet_diameter_max_in' must be greater than or equal to 'droplet_diameter_mean_in'."
        )

    water_mass_flow_rate = droplet_injection.get("water_mass_flow_rate")
    if water_mass_flow_rate is not None:
        _require_positive(
            water_mass_flow_rate,
            "droplet_injection.water_mass_flow_rate",
        )


def _validate_models(raw_config: dict[str, Any]) -> None:
    models = raw_config.get("models", {})

    critical_weber_number = models.get("critical_weber_number")
    if critical_weber_number is not None:
        _require_positive(critical_weber_number, "models.critical_weber_number")

    breakup_factor_mean = models.get("breakup_factor_mean")
    if breakup_factor_mean is not None:
        _require_positive(breakup_factor_mean, "models.breakup_factor_mean")

    breakup_factor_max = models.get("breakup_factor_max")
    if breakup_factor_max is not None:
        _require_positive(breakup_factor_max, "models.breakup_factor_max")


def validate_semantic_config(raw_config: dict[str, Any]) -> dict[str, Any]:
    """Validate supported values and physical consistency of configuration data.
    """

    _validate_fluid_section(raw_config)
    _validate_boundary_conditions(raw_config)
    _validate_geometry(raw_config)
    _validate_droplet_injection(raw_config)
    _validate_models(raw_config)

    return raw_config