"""Runtime pre-solver diagnostics for geometry and grid foundations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from supersonic_atomizer.common import ConfigurationError
from supersonic_atomizer.domain import GeometryConfig

if TYPE_CHECKING:
    from supersonic_atomizer.geometry.geometry_model import GeometryModel


def validate_geometry_config_diagnostics(geometry_config: GeometryConfig) -> GeometryConfig:
    """Validate geometry inputs for malformed tabulated-domain and grid cases."""

    if geometry_config.x_end <= geometry_config.x_start:
        raise ConfigurationError(
            f"Invalid axial range: x_end ({geometry_config.x_end}) must be greater than x_start ({geometry_config.x_start})."
        )

    if not isinstance(geometry_config.n_cells, int) or isinstance(geometry_config.n_cells, bool):
        raise ConfigurationError("Degenerate grid: geometry.n_cells must be an integer.")

    if geometry_config.n_cells <= 0:
        raise ConfigurationError("Degenerate grid: geometry.n_cells must be greater than zero.")

    area_definition = geometry_config.area_definition
    if area_definition.get("type") != "table":
        raise ConfigurationError("Unsupported geometry area profile type: expected 'table'.")

    x_values = area_definition.get("x")
    area_values = area_definition.get("A")
    if not isinstance(x_values, list) or not isinstance(area_values, list):
        raise ConfigurationError("Inconsistent area table: geometry.area_definition.x and A must be lists.")

    if len(x_values) != len(area_values):
        raise ConfigurationError(
            "Inconsistent area table lengths: geometry.area_definition.x and A must have the same length."
        )

    if len(x_values) < 2:
        raise ConfigurationError("Inconsistent area table: at least two tabulated points are required.")

    for index, area_value in enumerate(area_values):
        if area_value <= 0.0:
            raise ConfigurationError(
                f"Nonpositive area value at index {index}: area must be greater than zero."
            )

    for index in range(1, len(x_values)):
        if x_values[index] <= x_values[index - 1]:
            raise ConfigurationError(
                "Invalid tabulated ordering: geometry.area_definition.x must be strictly increasing."
            )

    if x_values[0] != geometry_config.x_start or x_values[-1] != geometry_config.x_end:
        raise ConfigurationError(
            "Geometry/profile consistency error: area-table endpoints must match geometry.x_start and geometry.x_end."
        )

    return geometry_config


def validate_geometry_model_diagnostics(geometry_model: GeometryModel) -> GeometryModel:
    """Validate assembled geometry/grid alignment before solver execution."""

    if geometry_model.length <= 0.0:
        raise ConfigurationError("Invalid geometry length: assembled geometry length must be positive.")

    if geometry_model.grid.node_count != geometry_model.grid.cell_count + 1:
        raise ConfigurationError(
            "Degenerate grid: node_count must equal cell_count + 1 for the uniform MVP grid."
        )

    if geometry_model.grid.x_nodes[0] != geometry_model.x_start:
        raise ConfigurationError("Geometry/grid consistency error: first grid node must equal geometry.x_start.")

    if geometry_model.grid.x_nodes[-1] != geometry_model.x_end:
        raise ConfigurationError("Geometry/grid consistency error: last grid node must equal geometry.x_end.")

    for index, dx_value in enumerate(geometry_model.grid.dx_values):
        if dx_value <= 0.0:
            raise ConfigurationError(
                f"Degenerate grid spacing at index {index}: spacing must be greater than zero."
            )

    for index, x_node in enumerate(geometry_model.grid.x_nodes):
        if not geometry_model.area_profile.supports(x_node):
            raise ConfigurationError(
                f"Geometry/grid consistency error: grid node at index {index} lies outside the supported area-profile domain."
            )

    return geometry_model