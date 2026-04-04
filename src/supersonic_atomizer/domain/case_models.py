"""Runtime case-configuration models.

These models represent validated case inputs only. They must remain free of
YAML parsing behavior, solver logic, provider instantiation, and output logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class FluidConfig:
    """Validated working-fluid configuration."""

    working_fluid: str
    inlet_wetness: float | None = None


@dataclass(frozen=True, slots=True)
class BoundaryConditionConfig:
    """Validated gas-side boundary conditions in SI units."""

    Pt_in: float
    Tt_in: float
    Ps_out: float


@dataclass(frozen=True, slots=True)
class GeometryConfig:
    """Validated geometry definition for later grid/geometry construction."""

    x_start: float
    x_end: float
    n_cells: int
    area_definition: dict[str, Any]


@dataclass(frozen=True, slots=True)
class DropletInjectionConfig:
    """Validated representative droplet-injection inputs."""

    droplet_velocity_in: float
    droplet_diameter_mean_in: float
    droplet_diameter_max_in: float
    water_mass_flow_rate: float | None = None


@dataclass(frozen=True, slots=True)
class ModelSelectionConfig:
    """Validated model selectors and tunable model parameters."""

    drag_model: str = "standard_sphere"
    breakup_model: str = "weber_critical"
    critical_weber_number: float = 12.0
    breakup_factor_mean: float | None = None
    breakup_factor_max: float | None = None
    steam_property_model: str | None = None


@dataclass(frozen=True, slots=True)
class OutputConfig:
    """Validated output preferences for writers and plotting."""

    output_directory: str = "outputs"
    write_csv: bool = True
    write_json: bool = True
    generate_plots: bool = True


@dataclass(frozen=True, slots=True)
class CaseConfig:
    """Validated top-level case configuration."""

    fluid: FluidConfig
    boundary_conditions: BoundaryConditionConfig
    geometry: GeometryConfig
    droplet_injection: DropletInjectionConfig
    models: ModelSelectionConfig
    outputs: OutputConfig
    case_name: str | None = None
    case_description: str | None = None
    config_version: str | int | None = None