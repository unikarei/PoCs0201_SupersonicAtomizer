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
    droplet_density: float = 998.2
    droplet_sphericity: float = 1.0
    breakup_model: str = "weber_critical"
    critical_weber_number: float = 12.0
    breakup_factor_mean: float | None = None
    breakup_factor_max: float | None = None
    steam_property_model: str | None = None
    gas_solver_mode: str = "baseline"
    coupling_mode: str = "one_way"
    two_way_max_iterations: int = 3
    two_way_feedback_relaxation: float = 0.35
    two_way_convergence_tolerance: float = 1.0e-3
    droplet_distribution_model: str = "mono"
    droplet_distribution_sigma: float = 0.35
    khrt_B0: float = 0.61
    khrt_B1: float = 40.0
    khrt_Crt: float = 0.1
    liquid_density: float = 998.2
    liquid_viscosity: float = 1.002e-3


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