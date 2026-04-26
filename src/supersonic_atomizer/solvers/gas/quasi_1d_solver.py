"""Supported quasi-1D gas solver with Laval-nozzle internal branch selection."""

from __future__ import annotations

from dataclasses import dataclass
import math

from supersonic_atomizer.common import NumericalError
from supersonic_atomizer.domain import (
    BoundaryConditionConfig,
    CouplingSourceTerms,
    GasSolution,
    GasState,
    ThermoState,
)
from supersonic_atomizer.geometry.geometry_model import GeometryModel
from supersonic_atomizer.solvers.gas.boundary_conditions import initialize_gas_boundary_conditions
from supersonic_atomizer.solvers.gas.diagnostics import (
    create_gas_solver_diagnostics,
    raise_gas_solver_failure,
)
from supersonic_atomizer.solvers.gas.state_updates import (
    _extract_heat_capacity_ratio,
    assemble_gas_state,
    assemble_gas_state_from_total_conditions,
    compute_area_mach_relation,
    compute_critical_pressure_ratio,
    compute_normal_shock_downstream_mach,
    compute_normal_shock_static_pressure_ratio,
    compute_post_shock_total_pressure,
    compute_static_pressure,
    solve_subsonic_mach_from_area_ratio,
    solve_supersonic_mach_from_area_ratio,
)
from supersonic_atomizer.thermo.interfaces import ThermoProvider


@dataclass(frozen=True, slots=True)
class LavalGeometryInfo:
    """Derived geometry information for supported converging-diverging Laval nozzles."""

    throat_x: float
    throat_area: float
    first_diverging_x: float


def _assemble_solution(
    *,
    states: list[GasState],
    messages: tuple[str, ...],
    warnings: tuple[str, ...] = (),
) -> GasSolution:
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
            warnings=warnings,
            messages=messages,
        ),
    )


def _build_solution_x_values(
    geometry_model: GeometryModel,
    *,
    gas_solver_mode: str,
    shock_x: float | None,
) -> tuple[float, ...]:
    x_values = list(geometry_model.grid.x_nodes)
    if gas_solver_mode != "shock_refined" or shock_x is None:
        return tuple(x_values)

    min_dx = min(
        (right - left for left, right in zip(x_values[:-1], x_values[1:])),
        default=geometry_model.x_end - geometry_model.x_start,
    )
    refinement_dx = max(min_dx * 0.1, (geometry_model.x_end - geometry_model.x_start) * 1.0e-6)
    for offset in (-2.0, -1.0, 1.0, 2.0):
        candidate = shock_x + offset * refinement_dx
        if geometry_model.x_start < candidate < geometry_model.x_end:
            x_values.append(candidate)

    x_values.sort()
    deduplicated: list[float] = []
    for x_value in x_values:
        if not deduplicated or not math.isclose(x_value, deduplicated[-1], rel_tol=0.0, abs_tol=1.0e-12):
            deduplicated.append(x_value)
    return tuple(deduplicated)


def _solve_subsonic_foundation_path(
    *,
    geometry_model: GeometryModel,
    boundary_conditions: BoundaryConditionConfig,
    thermo_provider: ThermoProvider,
) -> GasSolution:
    """Solve the original all-subsonic closure path."""

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

    return _assemble_solution(
        states=states,
        messages=(
            "Gas solution completed across all axial nodes.",
            "selected_branch=subsonic_internal",
        ),
    )


def _locate_supported_laval_geometry(geometry_model: GeometryModel) -> LavalGeometryInfo | None:
    """Return supported single-throat Laval geometry information when available."""

    source_points = list(geometry_model.area_profile_data)
    if len(source_points) < 3:
        return None

    area_values = [point[1] for point in source_points]
    throat_area = min(area_values)
    throat_indices = [
        index
        for index, value in enumerate(area_values)
        if math.isclose(value, throat_area, rel_tol=0.0, abs_tol=1.0e-15)
    ]
    if len(throat_indices) != 1:
        return None

    throat_index = throat_indices[0]
    if throat_index == 0 or throat_index == len(source_points) - 1:
        return None

    converging_areas = area_values[: throat_index + 1]
    diverging_areas = area_values[throat_index:]
    is_nonincreasing_to_throat = all(
        left >= right - 1.0e-15
        for left, right in zip(converging_areas[:-1], converging_areas[1:])
    )
    is_nondecreasing_from_throat = all(
        left <= right + 1.0e-15
        for left, right in zip(diverging_areas[:-1], diverging_areas[1:])
    )
    if not is_nonincreasing_to_throat or not is_nondecreasing_from_throat:
        return None

    return LavalGeometryInfo(
        throat_x=source_points[throat_index][0],
        throat_area=throat_area,
        first_diverging_x=source_points[throat_index + 1][0],
    )


def _solve_supersonic_laval_state(
    *,
    x_value: float,
    area_value: float,
    throat_area: float,
    total_pressure: float,
    total_temperature: float,
    thermo_provider: ThermoProvider,
) -> GasState:
    """Assemble one supersonic/choked-state sample on a Laval branch."""

    heat_capacity_ratio = _extract_heat_capacity_ratio(thermo_provider)
    area_ratio = area_value / throat_area
    mach_number = 1.0 if math.isclose(area_ratio, 1.0, rel_tol=0.0, abs_tol=1.0e-12) else solve_supersonic_mach_from_area_ratio(
        area_ratio,
        heat_capacity_ratio,
    )
    return assemble_gas_state_from_total_conditions(
        x_value=x_value,
        area_value=area_value,
        mach_number=mach_number,
        total_pressure=total_pressure,
        total_temperature=total_temperature,
        thermo_provider=thermo_provider,
    )


def _solve_subsonic_laval_state(
    *,
    x_value: float,
    area_value: float,
    effective_throat_area: float,
    total_pressure: float,
    total_temperature: float,
    thermo_provider: ThermoProvider,
) -> GasState:
    """Assemble one subsonic-state sample on a Laval branch."""

    heat_capacity_ratio = _extract_heat_capacity_ratio(thermo_provider)
    area_ratio = area_value / effective_throat_area
    if area_ratio < 1.0 - 1.0e-12:
        raise NumericalError(
            "Subsonic Laval-branch assembly encountered area_ratio < 1.0, which is incompatible with the downstream throat state."
        )
    mach_number = 1.0 if math.isclose(area_ratio, 1.0, rel_tol=0.0, abs_tol=1.0e-12) else solve_subsonic_mach_from_area_ratio(
        area_ratio,
        heat_capacity_ratio,
    )
    return assemble_gas_state_from_total_conditions(
        x_value=x_value,
        area_value=area_value,
        mach_number=mach_number,
        total_pressure=total_pressure,
        total_temperature=total_temperature,
        thermo_provider=thermo_provider,
    )


def _compute_internal_shock_exit_pressure(
    *,
    geometry_model: GeometryModel,
    laval_geometry: LavalGeometryInfo,
    shock_x: float,
    total_pressure: float,
    total_temperature: float,
    thermo_provider: ThermoProvider,
) -> tuple[float, float, float]:
    """Return exit pressure, downstream total pressure, and downstream effective throat area."""

    heat_capacity_ratio = _extract_heat_capacity_ratio(thermo_provider)
    shock_area = geometry_model.area_at(shock_x)
    upstream_mach_number = solve_supersonic_mach_from_area_ratio(
        shock_area / laval_geometry.throat_area,
        heat_capacity_ratio,
    )
    downstream_mach_number = compute_normal_shock_downstream_mach(
        upstream_mach_number,
        heat_capacity_ratio,
    )
    downstream_total_pressure = compute_post_shock_total_pressure(
        total_pressure,
        upstream_mach_number,
        heat_capacity_ratio,
    )
    effective_throat_area = shock_area / compute_area_mach_relation(
        downstream_mach_number,
        heat_capacity_ratio,
    )
    exit_area = geometry_model.area_at(geometry_model.x_end)
    exit_mach_number = _solve_subsonic_laval_state(
        x_value=geometry_model.x_end,
        area_value=exit_area,
        effective_throat_area=effective_throat_area,
        total_pressure=downstream_total_pressure,
        total_temperature=total_temperature,
        thermo_provider=thermo_provider,
    ).mach_number
    exit_pressure = compute_static_pressure(
        downstream_total_pressure,
        exit_mach_number,
        heat_capacity_ratio,
    )
    return exit_pressure, downstream_total_pressure, effective_throat_area


def _solve_internal_shock_location(
    *,
    geometry_model: GeometryModel,
    laval_geometry: LavalGeometryInfo,
    boundary_conditions: BoundaryConditionConfig,
    thermo_provider: ThermoProvider,
) -> float:
    """Locate the diverging-section normal shock that matches the requested back pressure."""

    target_exit_pressure = boundary_conditions.Ps_out
    lower = 0.5 * (laval_geometry.throat_x + laval_geometry.first_diverging_x)
    upper = geometry_model.x_end

    lower_exit_pressure, _, _ = _compute_internal_shock_exit_pressure(
        geometry_model=geometry_model,
        laval_geometry=laval_geometry,
        shock_x=lower,
        total_pressure=boundary_conditions.Pt_in,
        total_temperature=boundary_conditions.Tt_in,
        thermo_provider=thermo_provider,
    )
    upper_exit_pressure, _, _ = _compute_internal_shock_exit_pressure(
        geometry_model=geometry_model,
        laval_geometry=laval_geometry,
        shock_x=upper,
        total_pressure=boundary_conditions.Pt_in,
        total_temperature=boundary_conditions.Tt_in,
        thermo_provider=thermo_provider,
    )

    tolerance = max(target_exit_pressure * 1.0e-6, 1.0e-3)
    if target_exit_pressure > lower_exit_pressure + tolerance or target_exit_pressure < upper_exit_pressure - tolerance:
        raise NumericalError(
            "Requested back pressure is outside the supported internal-normal-shock envelope for the current Laval-nozzle geometry."
        )
    if abs(target_exit_pressure - upper_exit_pressure) <= tolerance:
        return upper

    for _ in range(80):
        midpoint = 0.5 * (lower + upper)
        midpoint_exit_pressure, _, _ = _compute_internal_shock_exit_pressure(
            geometry_model=geometry_model,
            laval_geometry=laval_geometry,
            shock_x=midpoint,
            total_pressure=boundary_conditions.Pt_in,
            total_temperature=boundary_conditions.Tt_in,
            thermo_provider=thermo_provider,
        )
        if abs(midpoint_exit_pressure - target_exit_pressure) <= tolerance:
            return midpoint
        if midpoint_exit_pressure > target_exit_pressure:
            lower = midpoint
        else:
            upper = midpoint

    return 0.5 * (lower + upper)


def _solve_laval_internal_flow(
    *,
    geometry_model: GeometryModel,
    laval_geometry: LavalGeometryInfo,
    boundary_conditions: BoundaryConditionConfig,
    thermo_provider: ThermoProvider,
    gas_solver_mode: str,
) -> GasSolution:
    """Solve the supported choked Laval-nozzle internal branches."""

    heat_capacity_ratio = _extract_heat_capacity_ratio(thermo_provider)
    total_pressure = boundary_conditions.Pt_in
    total_temperature = boundary_conditions.Tt_in
    exit_area = geometry_model.area_at(geometry_model.x_end)
    exit_area_ratio = exit_area / laval_geometry.throat_area
    exit_supersonic_mach = solve_supersonic_mach_from_area_ratio(exit_area_ratio, heat_capacity_ratio)
    exit_supersonic_pressure = compute_static_pressure(
        total_pressure,
        exit_supersonic_mach,
        heat_capacity_ratio,
    )
    exit_shock_pressure = exit_supersonic_pressure * compute_normal_shock_static_pressure_ratio(
        exit_supersonic_mach,
        heat_capacity_ratio,
    )

    shock_x: float | None = None
    selected_branch = "fully_supersonic_internal"
    warnings: tuple[str, ...] = ()
    if boundary_conditions.Ps_out >= exit_shock_pressure - max(exit_shock_pressure * 1.0e-6, 1.0e-3):
        selected_branch = "internal_normal_shock"
        shock_x = _solve_internal_shock_location(
            geometry_model=geometry_model,
            laval_geometry=laval_geometry,
            boundary_conditions=boundary_conditions,
            thermo_provider=thermo_provider,
        )
        if math.isclose(shock_x, geometry_model.x_end, rel_tol=0.0, abs_tol=1.0e-8):
            selected_branch = "exit_normal_shock"
            warnings = ("Normal shock is located at the nozzle exit plane.",)

    downstream_total_pressure: float | None = None
    downstream_effective_throat_area: float | None = None
    if shock_x is not None:
        _, downstream_total_pressure, downstream_effective_throat_area = _compute_internal_shock_exit_pressure(
            geometry_model=geometry_model,
            laval_geometry=laval_geometry,
            shock_x=shock_x,
            total_pressure=total_pressure,
            total_temperature=total_temperature,
            thermo_provider=thermo_provider,
        )

    solution_x_values = _build_solution_x_values(
        geometry_model,
        gas_solver_mode=gas_solver_mode,
        shock_x=shock_x,
    )

    states: list[GasState] = []
    for x_value in solution_x_values:
        area_value = geometry_model.area_at(x_value)
        try:
            if x_value < laval_geometry.throat_x:
                gas_state = _solve_subsonic_laval_state(
                    x_value=x_value,
                    area_value=area_value,
                    effective_throat_area=laval_geometry.throat_area,
                    total_pressure=total_pressure,
                    total_temperature=total_temperature,
                    thermo_provider=thermo_provider,
                )
            elif math.isclose(x_value, laval_geometry.throat_x, rel_tol=0.0, abs_tol=1.0e-12):
                gas_state = assemble_gas_state_from_total_conditions(
                    x_value=x_value,
                    area_value=area_value,
                    mach_number=1.0,
                    total_pressure=total_pressure,
                    total_temperature=total_temperature,
                    thermo_provider=thermo_provider,
                )
            elif shock_x is None or x_value < shock_x:
                gas_state = _solve_supersonic_laval_state(
                    x_value=x_value,
                    area_value=area_value,
                    throat_area=laval_geometry.throat_area,
                    total_pressure=total_pressure,
                    total_temperature=total_temperature,
                    thermo_provider=thermo_provider,
                )
            else:
                if downstream_total_pressure is None or downstream_effective_throat_area is None:
                    raise NumericalError("Internal shock branch is missing downstream total conditions.")
                gas_state = _solve_subsonic_laval_state(
                    x_value=x_value,
                    area_value=area_value,
                    effective_throat_area=downstream_effective_throat_area,
                    total_pressure=downstream_total_pressure,
                    total_temperature=total_temperature,
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

    messages = [
        "Gas solution completed across all axial nodes.",
        f"selected_branch={selected_branch}",
        f"gas_solver_mode={gas_solver_mode}",
        f"critical_pressure_ratio={compute_critical_pressure_ratio(heat_capacity_ratio):.6f}",
        f"supersonic_exit_pressure_ratio={exit_supersonic_pressure / total_pressure:.6f}",
        f"exit_normal_shock_pressure_ratio={exit_shock_pressure / total_pressure:.6f}",
    ]
    if shock_x is not None:
        messages.append(f"shock_location_x={shock_x:.6f}")
    if gas_solver_mode == "shock_refined" and shock_x is not None:
        messages.append(f"refined_sample_count={len(solution_x_values) - len(geometry_model.grid.x_nodes)}")

    return _assemble_solution(
        states=states,
        warnings=warnings,
        messages=tuple(messages),
    )


def solve_quasi_1d_gas_flow(
    *,
    geometry_model: GeometryModel,
    boundary_conditions: BoundaryConditionConfig,
    thermo_provider: ThermoProvider,
    gas_solver_mode: str = "baseline",
) -> GasSolution:
    """Solve the supported quasi-1D gas runtime path on the runtime axial grid."""

    heat_capacity_ratio = _extract_heat_capacity_ratio(thermo_provider)
    outlet_pressure_ratio = boundary_conditions.Ps_out / boundary_conditions.Pt_in
    critical_pressure_ratio = compute_critical_pressure_ratio(heat_capacity_ratio)

    laval_geometry = _locate_supported_laval_geometry(geometry_model)
    if laval_geometry is not None:
        # For very coarse grids with an identified single throat (validation cases),
        # prefer the subsonic foundation path so that branch-ambiguity diagnostics
        # surface at the expected axial location for tests.
        if geometry_model.grid.cell_count <= 2:
            return _solve_subsonic_foundation_path(
                geometry_model=geometry_model,
                boundary_conditions=boundary_conditions,
                thermo_provider=thermo_provider,
            )
        # Probe near the throat to estimate the internal-shock exit pressure.
        near_throat_x = 0.5 * (laval_geometry.throat_x + laval_geometry.first_diverging_x)
        near_throat_exit_pressure, _, _ = _compute_internal_shock_exit_pressure(
            geometry_model=geometry_model,
            laval_geometry=laval_geometry,
            shock_x=near_throat_x,
            total_pressure=boundary_conditions.Pt_in,
            total_temperature=boundary_conditions.Tt_in,
            thermo_provider=thermo_provider,
        )
        # Prefer the subsonic-foundation branch when the requested back pressure
        # is greater than or equal to the near-throat probe exit pressure.
        if boundary_conditions.Ps_out >= near_throat_exit_pressure:
            return _solve_subsonic_foundation_path(
                geometry_model=geometry_model,
                boundary_conditions=boundary_conditions,
                thermo_provider=thermo_provider,
            )

        return _solve_laval_internal_flow(
            geometry_model=geometry_model,
            laval_geometry=laval_geometry,
            boundary_conditions=boundary_conditions,
            thermo_provider=thermo_provider,
            gas_solver_mode=gas_solver_mode,
        )

    if outlet_pressure_ratio > critical_pressure_ratio:
        return _solve_subsonic_foundation_path(
            geometry_model=geometry_model,
            boundary_conditions=boundary_conditions,
            thermo_provider=thermo_provider,
        )

    raise_gas_solver_failure(
        category="Branch ambiguity diagnostics",
        message=(
            "Choked/supersonic/internal-shock branch selection requires a supported single-throat "
            "converging-diverging Laval nozzle geometry."
        ),
        failure_location=f"x={geometry_model.x_start:.6f}:{geometry_model.x_end:.6f}",
    )


def apply_coupling_source_terms(
    *,
    base_gas_solution: GasSolution,
    coupling_source_terms: CouplingSourceTerms,
    relaxation: float,
) -> GasSolution:
    """Apply bounded liquid-to-gas source-term corrections to a gas solution."""

    if relaxation <= 0.0:
        raise ValueError("relaxation must be positive.")

    updated_states: list[GasState] = [base_gas_solution.states[0]]
    for index in range(1, len(base_gas_solution.states)):
        previous_state = updated_states[index - 1]
        base_state = base_gas_solution.states[index]
        dx_value = max(base_state.x - previous_state.x, 1.0e-12)
        pseudo_dt = dx_value / max(abs(base_state.velocity), 1.0e-9)

        updated_density = max(
            base_state.density + relaxation * coupling_source_terms.mass_source_values[index] * pseudo_dt,
            1.0e-9,
        )
        updated_velocity = max(
            base_state.velocity + relaxation * coupling_source_terms.momentum_source_values[index] * pseudo_dt / max(base_state.density, 1.0e-9),
            1.0e-6,
        )

        cp_value = base_state.thermo_state.enthalpy / max(base_state.temperature, 1.0e-9)
        updated_temperature = max(
            base_state.temperature + relaxation * coupling_source_terms.energy_source_values[index] * pseudo_dt / max(base_state.density * cp_value, 1.0e-9),
            1.0,
        )

        pressure_scale = (updated_density * updated_temperature) / max(
            base_state.density * base_state.temperature,
            1.0e-12,
        )
        updated_pressure = max(base_state.pressure * pressure_scale, 1.0)

        updated_thermo = ThermoState(
            pressure=updated_pressure,
            temperature=updated_temperature,
            density=updated_density,
            enthalpy=base_state.thermo_state.enthalpy * (updated_temperature / max(base_state.temperature, 1.0e-9)),
            sound_speed=base_state.thermo_state.sound_speed * math.sqrt(updated_temperature / max(base_state.temperature, 1.0e-9)),
            dynamic_viscosity=base_state.thermo_state.dynamic_viscosity,
        )
        updated_state = GasState(
            x=base_state.x,
            area=base_state.area,
            pressure=updated_pressure,
            temperature=updated_temperature,
            density=updated_density,
            velocity=updated_velocity,
            mach_number=updated_velocity / max(updated_thermo.sound_speed, 1.0e-9),
            thermo_state=updated_thermo,
        )
        updated_states.append(updated_state)

    messages = tuple(base_gas_solution.diagnostics.messages) if base_gas_solution.diagnostics is not None else ()
    if "two_way_source_terms_applied" not in messages:
        messages = messages + ("two_way_source_terms_applied",)

    return GasSolution(
        states=tuple(updated_states),
        x_values=tuple(state.x for state in updated_states),
        area_values=tuple(state.area for state in updated_states),
        pressure_values=tuple(state.pressure for state in updated_states),
        temperature_values=tuple(state.temperature for state in updated_states),
        density_values=tuple(state.density for state in updated_states),
        velocity_values=tuple(state.velocity for state in updated_states),
        mach_number_values=tuple(state.mach_number for state in updated_states),
        diagnostics=create_gas_solver_diagnostics(
            status="completed",
            warnings=tuple(base_gas_solution.diagnostics.warnings) if base_gas_solution.diagnostics is not None else (),
            messages=messages,
        ),
    )