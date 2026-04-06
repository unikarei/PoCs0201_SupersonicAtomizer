"""Supported quasi-1D gas solver for the current air foundation path."""

from __future__ import annotations

from supersonic_atomizer.common import NumericalError
from supersonic_atomizer.domain import BoundaryConditionConfig, GasSolution, GasState
from supersonic_atomizer.geometry.geometry_model import GeometryModel
from supersonic_atomizer.solvers.gas.boundary_conditions import initialize_gas_boundary_conditions
from supersonic_atomizer.solvers.gas.diagnostics import (
    create_gas_solver_diagnostics,
    raise_gas_solver_failure,
)
from supersonic_atomizer.solvers.gas.state_updates import (
    _extract_heat_capacity_ratio,
    assemble_gas_state,
    compute_area_mach_relation,
    solve_subsonic_mach_from_area_ratio,
)
from supersonic_atomizer.thermo.interfaces import ThermoProvider


def solve_quasi_1d_gas_flow(
    *,
    geometry_model: GeometryModel,
    boundary_conditions: BoundaryConditionConfig,
    thermo_provider: ThermoProvider,
) -> GasSolution:
    """Solve the supported quasi-1D gas foundation path on the runtime axial grid."""

    boundary_state = initialize_gas_boundary_conditions(boundary_conditions, thermo_provider)
    heat_capacity_ratio = _extract_heat_capacity_ratio(thermo_provider)

    outlet_area = geometry_model.area_at(geometry_model.x_end)
    outlet_area_ratio = compute_area_mach_relation(
        boundary_state.outlet_mach_number,
        heat_capacity_ratio,
    )
    throat_area = outlet_area / outlet_area_ratio

    if throat_area <= 0.0:
        raise_gas_solver_failure(
            category="Failed closure diagnostics",
            message="Derived throat area is nonphysical.",
            failure_location=f"x={geometry_model.x_end:.6f}",
        )

    states: list[GasState] = []
    for x_value in geometry_model.grid.x_nodes:
        area_value = geometry_model.area_at(x_value)
        local_area_ratio = area_value / throat_area

        if local_area_ratio <= 1.0:
            raise_gas_solver_failure(
                category="Branch ambiguity diagnostics",
                message=(
                    "Subsonic foundation path encountered area_ratio <= 1.0 and cannot "
                    "continue without choking-aware branch selection."
                ),
                failure_location=f"x={x_value:.6f}",
                last_valid_state=states[-1] if states else None,
            )

        try:
            mach_number = solve_subsonic_mach_from_area_ratio(
                local_area_ratio,
                heat_capacity_ratio,
            )
            gas_state = assemble_gas_state(
                x_value=x_value,
                area_value=area_value,
                mach_number=mach_number,
                boundary_state=boundary_state,
                thermo_provider=thermo_provider,
            )
        except NumericalError as exc:
            raise_gas_solver_failure(
                category="Incomplete solution progression diagnostics",
                message=str(exc),
                failure_location=f"x={x_value:.6f}",
                last_valid_state=states[-1] if states else None,
            )

        states.append(gas_state)

    return GasSolution(
        states=tuple(states),
        x_values=tuple(state.x for state in states),
        area_values=tuple(state.area for state in states),
        pressure_values=tuple(state.pressure for state in states),
        temperature_values=tuple(state.temperature for state in states),
        density_values=tuple(state.density for state in states),
        velocity_values=tuple(state.velocity for state in states),
        mach_number_values=tuple(state.mach_number for state in states),
        diagnostics=create_gas_solver_diagnostics(
            status="completed",
            messages=("Gas solution completed across all axial nodes.",),
        ),
    )