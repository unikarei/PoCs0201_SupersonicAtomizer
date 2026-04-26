"""Configuration translation scaffold.

This module is reserved for translation from normalized external config data to
typed internal runtime models. It must not perform raw parsing or solver work.
"""

from __future__ import annotations

from typing import Any

from supersonic_atomizer.domain import (
    BoundaryConditionConfig,
    CaseConfig,
    DropletInjectionConfig,
    FluidConfig,
    GeometryConfig,
    ModelSelectionConfig,
    OutputConfig,
)


def _translate_fluid_config(raw_config: dict[str, Any]) -> FluidConfig:
    fluid_section = raw_config["fluid"]
    return FluidConfig(
        working_fluid=fluid_section["working_fluid"],
        inlet_wetness=fluid_section.get("inlet_wetness"),
    )


def _translate_boundary_conditions(raw_config: dict[str, Any]) -> BoundaryConditionConfig:
    boundary_section = raw_config["boundary_conditions"]
    return BoundaryConditionConfig(
        Pt_in=boundary_section["Pt_in"],
        Tt_in=boundary_section["Tt_in"],
        Ps_out=boundary_section["Ps_out"],
    )


def _translate_geometry_config(raw_config: dict[str, Any]) -> GeometryConfig:
    geometry_section = raw_config["geometry"]
    return GeometryConfig(
        x_start=geometry_section["x_start"],
        x_end=geometry_section["x_end"],
        n_cells=geometry_section["n_cells"],
        area_definition=geometry_section["area_distribution"],
    )


def _translate_droplet_injection(raw_config: dict[str, Any]) -> DropletInjectionConfig:
    droplet_section = raw_config["droplet_injection"]
    return DropletInjectionConfig(
        droplet_velocity_in=droplet_section["droplet_velocity_in"],
        droplet_diameter_mean_in=droplet_section["droplet_diameter_mean_in"],
        droplet_diameter_max_in=droplet_section["droplet_diameter_max_in"],
        water_mass_flow_rate=droplet_section.get("water_mass_flow_rate"),
    )


def _translate_model_selection(raw_config: dict[str, Any]) -> ModelSelectionConfig:
    models_section = raw_config.get("models", {})
    return ModelSelectionConfig(
        drag_model=models_section.get("drag_model", "standard_sphere"),
        droplet_density=models_section.get("droplet_density", 998.2),
        droplet_sphericity=models_section.get("droplet_sphericity", 1.0),
        breakup_model=models_section.get("breakup_model", "weber_critical"),
        critical_weber_number=models_section.get("critical_weber_number", 12.0),
        breakup_factor_mean=models_section.get("breakup_factor_mean"),
        breakup_factor_max=models_section.get("breakup_factor_max"),
        steam_property_model=models_section.get("steam_property_model"),
        gas_solver_mode=models_section.get("gas_solver_mode", "baseline"),
        coupling_mode=models_section.get("coupling_mode", "one_way"),
        two_way_max_iterations=models_section.get("two_way_max_iterations", 3),
        two_way_feedback_relaxation=models_section.get("two_way_feedback_relaxation", 0.35),
        two_way_convergence_tolerance=models_section.get("two_way_convergence_tolerance", 1.0e-3),
        droplet_distribution_model=models_section.get("droplet_distribution_model", "mono"),
        droplet_distribution_sigma=models_section.get("droplet_distribution_sigma", 0.35),
        khrt_B0=models_section.get("khrt_B0", 0.61),
        khrt_B1=models_section.get("khrt_B1", 40.0),
        khrt_Crt=models_section.get("khrt_Crt", 0.1),
        liquid_density=models_section.get("liquid_density", 998.2),
        liquid_viscosity=models_section.get("liquid_viscosity", 1.002e-3),
    )


def _translate_output_config(raw_config: dict[str, Any]) -> OutputConfig:
    outputs_section = raw_config.get("outputs", {})
    return OutputConfig(
        output_directory=outputs_section.get("output_directory", "outputs"),
        write_csv=outputs_section.get("write_csv", True),
        write_json=outputs_section.get("write_json", True),
        generate_plots=outputs_section.get("generate_plots", True),
    )


def translate_case_config(raw_config: dict[str, Any]) -> CaseConfig:
    """Translate normalized config data into internal runtime models."""

    case_section = raw_config.get("case", {})
    return CaseConfig(
        case_name=case_section.get("name"),
        case_description=case_section.get("description"),
        config_version=case_section.get("config_version"),
        fluid=_translate_fluid_config(raw_config),
        boundary_conditions=_translate_boundary_conditions(raw_config),
        geometry=_translate_geometry_config(raw_config),
        droplet_injection=_translate_droplet_injection(raw_config),
        models=_translate_model_selection(raw_config),
        outputs=_translate_output_config(raw_config),
    )