"""Runtime geometry assembly for validated case geometry inputs."""

from __future__ import annotations

from dataclasses import dataclass

from supersonic_atomizer.common import ConfigurationError
from supersonic_atomizer.domain import GeometryConfig
from supersonic_atomizer.geometry.area_profile import (
    TabulatedAreaProfile,
    build_tabulated_area_profile,
)
from supersonic_atomizer.grid import AxialGrid, build_axial_grid


@dataclass(frozen=True, slots=True)
class GeometryModel:
    """Runtime geometry object combining domain metadata, grid, and area profile."""

    x_start: float
    x_end: float
    length: float
    area_profile_type: str
    area_profile_data: tuple[tuple[float, float], ...]
    is_tabulated_profile: bool
    grid: AxialGrid
    area_profile: TabulatedAreaProfile
    domain_label: str | None = None
    source_description: str | None = None

    def __post_init__(self) -> None:
        if self.length <= 0.0:
            raise ConfigurationError("Geometry length must be positive.")

        if self.grid.x_start != self.x_start or self.grid.x_end != self.x_end:
            raise ConfigurationError("Geometry grid domain must align with geometry axial range.")

        if self.area_profile.x_min != self.x_start or self.area_profile.x_max != self.x_end:
            raise ConfigurationError("Geometry area-profile domain must align with geometry axial range.")

        if self.area_profile_type != self.area_profile.profile_type:
            raise ConfigurationError("Geometry area_profile_type must match the runtime area profile type.")

        if self.is_tabulated_profile != self.area_profile.is_tabulated:
            raise ConfigurationError("Geometry tabulated-profile flag must match the runtime area profile.")

        if self.area_profile_data != self.area_profile.source_points:
            raise ConfigurationError("Geometry area_profile_data must match the runtime area profile source points.")

    def supports(self, x_value: float) -> bool:
        return self.area_profile.supports(x_value)

    def area_at(self, x_value: float) -> float:
        return self.area_profile.area_at(x_value)


def build_geometry_model(geometry_config: GeometryConfig) -> GeometryModel:
    """Assemble the runtime geometry model from validated geometry configuration."""

    from supersonic_atomizer.geometry.diagnostics import (
        validate_geometry_config_diagnostics,
        validate_geometry_model_diagnostics,
    )

    validate_geometry_config_diagnostics(geometry_config)

    grid = build_axial_grid(geometry_config)
    area_profile = build_tabulated_area_profile(geometry_config)

    geometry_model = GeometryModel(
        x_start=geometry_config.x_start,
        x_end=geometry_config.x_end,
        length=geometry_config.x_end - geometry_config.x_start,
        area_profile_type=area_profile.profile_type,
        area_profile_data=area_profile.source_points,
        is_tabulated_profile=area_profile.is_tabulated,
        grid=grid,
        area_profile=area_profile,
    )

    return validate_geometry_model_diagnostics(geometry_model)