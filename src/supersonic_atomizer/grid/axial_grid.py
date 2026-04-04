"""Runtime axial-grid model and construction helpers."""

from __future__ import annotations

from dataclasses import dataclass

from supersonic_atomizer.common import ConfigurationError
from supersonic_atomizer.domain import GeometryConfig


def _validate_node_sequence(x_nodes: tuple[float, ...]) -> None:
    if len(x_nodes) < 2:
        raise ConfigurationError("Axial grid must contain at least two nodes.")

    for left, right in zip(x_nodes, x_nodes[1:]):
        if right <= left:
            raise ConfigurationError("Axial grid nodes must be strictly increasing.")


@dataclass(frozen=True, slots=True)
class AxialGrid:
    """Uniform runtime axial grid for solver marching and profile alignment."""

    x_nodes: tuple[float, ...]
    dx_values: tuple[float, ...]
    x_start: float
    x_end: float
    nominal_dx: float
    is_uniform: bool
    node_count: int
    cell_count: int
    domain_length: float

    def __post_init__(self) -> None:
        _validate_node_sequence(self.x_nodes)

        if self.x_nodes[0] != self.x_start:
            raise ConfigurationError("Axial grid start node must match x_start.")

        if self.x_nodes[-1] != self.x_end:
            raise ConfigurationError("Axial grid end node must match x_end.")

        if self.cell_count != len(self.x_nodes) - 1:
            raise ConfigurationError("Axial grid cell_count must equal node_count - 1.")

        if self.node_count != len(self.x_nodes):
            raise ConfigurationError("Axial grid node_count must match x_nodes length.")

        if len(self.dx_values) != self.cell_count:
            raise ConfigurationError("Axial grid dx_values length must equal cell_count.")

        if self.domain_length <= 0.0:
            raise ConfigurationError("Axial grid domain length must be positive.")

        if self.nominal_dx <= 0.0:
            raise ConfigurationError("Axial grid nominal_dx must be positive.")

        for dx in self.dx_values:
            if dx <= 0.0:
                raise ConfigurationError("Axial grid spacing values must be positive.")


def build_axial_grid(geometry_config: GeometryConfig) -> AxialGrid:
    """Build a uniform runtime axial grid from validated geometry inputs."""

    if geometry_config.x_end <= geometry_config.x_start:
        raise ConfigurationError("Geometry x_end must be greater than x_start.")

    if not isinstance(geometry_config.n_cells, int) or isinstance(geometry_config.n_cells, bool):
        raise ConfigurationError("Geometry n_cells must be an integer.")

    if geometry_config.n_cells <= 0:
        raise ConfigurationError("Geometry n_cells must be greater than zero.")

    domain_length = geometry_config.x_end - geometry_config.x_start
    nominal_dx = domain_length / geometry_config.n_cells
    x_nodes = tuple(
        geometry_config.x_start + index * nominal_dx
        for index in range(geometry_config.n_cells)
    ) + (geometry_config.x_end,)
    dx_values = tuple(
        right - left for left, right in zip(x_nodes, x_nodes[1:])
    )

    return AxialGrid(
        x_nodes=x_nodes,
        dx_values=dx_values,
        x_start=geometry_config.x_start,
        x_end=geometry_config.x_end,
        nominal_dx=nominal_dx,
        is_uniform=True,
        node_count=len(x_nodes),
        cell_count=geometry_config.n_cells,
        domain_length=domain_length,
    )