"""Runtime tabulated area-profile model."""

from __future__ import annotations

from dataclasses import dataclass

from supersonic_atomizer.common import ConfigurationError
from supersonic_atomizer.domain import GeometryConfig


def _validate_tabulated_points(
    x_points: tuple[float, ...],
    area_values: tuple[float, ...],
) -> None:
    if len(x_points) != len(area_values):
        raise ConfigurationError("Tabulated area-profile x and A arrays must have the same length.")

    if len(x_points) < 2:
        raise ConfigurationError("Tabulated area profile must contain at least two points.")

    for area_value in area_values:
        if area_value <= 0.0:
            raise ConfigurationError("Tabulated area-profile values must be positive.")

    for left, right in zip(x_points, x_points[1:]):
        if right <= left:
            raise ConfigurationError("Tabulated area-profile x values must be strictly increasing.")


@dataclass(frozen=True, slots=True)
class TabulatedAreaProfile:
    """Validated runtime storage for tabulated $(x, A)$ geometry data."""

    x_points: tuple[float, ...]
    area_values: tuple[float, ...]
    profile_type: str = "table"
    is_tabulated: bool = True

    def __post_init__(self) -> None:
        if self.profile_type != "table":
            raise ConfigurationError("Runtime area profile currently supports only 'table' type.")

        _validate_tabulated_points(self.x_points, self.area_values)

    @property
    def x_min(self) -> float:
        return self.x_points[0]

    @property
    def x_max(self) -> float:
        return self.x_points[-1]

    @property
    def source_points(self) -> tuple[tuple[float, float], ...]:
        return tuple(zip(self.x_points, self.area_values))

    def supports(self, x_value: float) -> bool:
        return self.x_min <= x_value <= self.x_max

    def area_at(self, x_value: float) -> float:
        """Return tabulated area by exact-match or piecewise-linear interpolation."""

        if not self.supports(x_value):
            raise ConfigurationError("Area query lies outside the supported tabulated domain.")

        for x_point, area_value in self.source_points:
            if x_value == x_point:
                return area_value

        for left_x, right_x, left_area, right_area in zip(
            self.x_points,
            self.x_points[1:],
            self.area_values,
            self.area_values[1:],
        ):
            if left_x < x_value < right_x:
                interval_fraction = (x_value - left_x) / (right_x - left_x)
                return left_area + interval_fraction * (right_area - left_area)

        raise ConfigurationError("Area query could not be bracketed within the tabulated domain.")


def build_tabulated_area_profile(geometry_config: GeometryConfig) -> TabulatedAreaProfile:
    """Build a runtime tabulated area profile from validated geometry config."""

    area_definition = geometry_config.area_definition
    profile_type = area_definition.get("type")
    if profile_type != "table":
        raise ConfigurationError("Geometry area_definition.type must be 'table' for the MVP.")

    x_points = tuple(area_definition["x"])
    area_values = tuple(area_definition["A"])

    return TabulatedAreaProfile(
        x_points=x_points,
        area_values=area_values,
        profile_type=profile_type,
        is_tabulated=True,
    )