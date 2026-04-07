"""Gas-state update helpers for the supported quasi-1D foundation path."""

from __future__ import annotations

import math

from supersonic_atomizer.common import NumericalError, ThermoError
from supersonic_atomizer.domain import GasState, ThermoState
from supersonic_atomizer.solvers.gas.boundary_conditions import GasBoundaryConditionState
from supersonic_atomizer.thermo import evaluate_thermo_state
from supersonic_atomizer.thermo.interfaces import ThermoProvider


def _extract_heat_capacity_ratio(thermo_provider: ThermoProvider) -> float:
    gamma = getattr(thermo_provider, "heat_capacity_ratio", None)
    if not isinstance(gamma, (int, float)) or gamma <= 1.0:
        raise ThermoError(
            "The supported gas-state update path requires a thermo provider with a valid "
            "'heat_capacity_ratio' attribute."
        )
    return float(gamma)


def compute_area_mach_relation(mach_number: float, heat_capacity_ratio: float) -> float:
    """Compute the standard quasi-1D area-to-throat ratio for a positive Mach number."""

    if mach_number <= 0.0 or not math.isfinite(mach_number):
        raise NumericalError("Area-Mach relation requires a positive finite Mach number.")

    ratio_term = (2.0 / (heat_capacity_ratio + 1.0)) * (
        1.0 + (heat_capacity_ratio - 1.0) * mach_number**2 / 2.0
    )
    exponent = (heat_capacity_ratio + 1.0) / (2.0 * (heat_capacity_ratio - 1.0))
    return (1.0 / mach_number) * ratio_term**exponent


def solve_subsonic_mach_from_area_ratio(
    area_ratio: float,
    heat_capacity_ratio: float,
    *,
    tolerance: float = 1.0e-10,
    max_iterations: int = 200,
) -> float:
    """Solve the subsonic Mach number for a supported area ratio using bisection."""

    if area_ratio <= 1.0:
        raise NumericalError(
            f"Subsonic area-ratio inversion requires area_ratio > 1.0, got {area_ratio}."
        )

    lower = 1.0e-8
    upper = 1.0 - 1.0e-8
    for _ in range(max_iterations):
        midpoint = 0.5 * (lower + upper)
        midpoint_ratio = compute_area_mach_relation(midpoint, heat_capacity_ratio)
        if abs(midpoint_ratio - area_ratio) <= tolerance:
            return midpoint
        if midpoint_ratio > area_ratio:
            lower = midpoint
        else:
            upper = midpoint

    return 0.5 * (lower + upper)


def solve_supersonic_mach_from_area_ratio(
    area_ratio: float,
    heat_capacity_ratio: float,
    *,
    tolerance: float = 1.0e-10,
    max_iterations: int = 200,
    upper_bound: float = 50.0,
) -> float:
    """Solve the supersonic Mach number for a supported area ratio using bisection."""

    if area_ratio < 1.0:
        raise NumericalError(
            f"Supersonic area-ratio inversion requires area_ratio >= 1.0, got {area_ratio}."
        )
    if area_ratio == 1.0:
        return 1.0

    lower = 1.0 + 1.0e-8
    upper = upper_bound
    if compute_area_mach_relation(upper, heat_capacity_ratio) < area_ratio:
        raise NumericalError(
            "Supersonic area-ratio inversion upper bound is too small for the requested area ratio."
        )

    for _ in range(max_iterations):
        midpoint = 0.5 * (lower + upper)
        midpoint_ratio = compute_area_mach_relation(midpoint, heat_capacity_ratio)
        if abs(midpoint_ratio - area_ratio) <= tolerance:
            return midpoint
        if midpoint_ratio < area_ratio:
            lower = midpoint
        else:
            upper = midpoint

    return 0.5 * (lower + upper)


def compute_critical_pressure_ratio(heat_capacity_ratio: float) -> float:
    """Compute the critical static-to-total pressure ratio for sonic flow."""

    return (2.0 / (heat_capacity_ratio + 1.0)) ** (
        heat_capacity_ratio / (heat_capacity_ratio - 1.0)
    )


def compute_static_temperature(
    total_temperature: float,
    mach_number: float,
    heat_capacity_ratio: float,
) -> float:
    """Compute static temperature from total temperature and Mach number."""

    static_temperature = total_temperature / (
        1.0 + (heat_capacity_ratio - 1.0) * mach_number**2 / 2.0
    )
    if static_temperature <= 0.0 or not math.isfinite(static_temperature):
        raise NumericalError("Computed a nonphysical static temperature in gas-state update.")
    return static_temperature


def compute_static_pressure(
    total_pressure: float,
    mach_number: float,
    heat_capacity_ratio: float,
) -> float:
    """Compute static pressure from total pressure and Mach number."""

    static_pressure = total_pressure / (
        1.0 + (heat_capacity_ratio - 1.0) * mach_number**2 / 2.0
    ) ** (heat_capacity_ratio / (heat_capacity_ratio - 1.0))
    if static_pressure <= 0.0 or not math.isfinite(static_pressure):
        raise NumericalError("Computed a nonphysical static pressure in gas-state update.")
    return static_pressure


def compute_total_pressure(
    static_pressure: float,
    mach_number: float,
    heat_capacity_ratio: float,
) -> float:
    """Compute total pressure from static pressure and Mach number."""

    if static_pressure <= 0.0 or not math.isfinite(static_pressure):
        raise NumericalError("Total-pressure evaluation requires a positive finite static pressure.")
    if mach_number <= 0.0 or not math.isfinite(mach_number):
        raise NumericalError("Total-pressure evaluation requires a positive finite Mach number.")

    total_pressure = static_pressure * (
        1.0 + (heat_capacity_ratio - 1.0) * mach_number**2 / 2.0
    ) ** (heat_capacity_ratio / (heat_capacity_ratio - 1.0))
    if total_pressure <= 0.0 or not math.isfinite(total_pressure):
        raise NumericalError("Computed a nonphysical total pressure in gas-state update.")
    return total_pressure


def compute_normal_shock_downstream_mach(
    upstream_mach_number: float,
    heat_capacity_ratio: float,
) -> float:
    """Compute the downstream Mach number across a normal shock."""

    if upstream_mach_number <= 1.0 or not math.isfinite(upstream_mach_number):
        raise NumericalError("Normal-shock relations require an upstream Mach number greater than 1.0.")

    numerator = (heat_capacity_ratio - 1.0) * upstream_mach_number**2 + 2.0
    denominator = 2.0 * heat_capacity_ratio * upstream_mach_number**2 - (heat_capacity_ratio - 1.0)
    downstream_mach_number = math.sqrt(numerator / denominator)
    if downstream_mach_number <= 0.0 or not math.isfinite(downstream_mach_number):
        raise NumericalError("Computed a nonphysical downstream Mach number across a normal shock.")
    return downstream_mach_number


def compute_normal_shock_static_pressure_ratio(
    upstream_mach_number: float,
    heat_capacity_ratio: float,
) -> float:
    """Compute the static-pressure ratio across a normal shock."""

    if upstream_mach_number <= 1.0 or not math.isfinite(upstream_mach_number):
        raise NumericalError("Normal-shock relations require an upstream Mach number greater than 1.0.")

    pressure_ratio = 1.0 + (
        2.0 * heat_capacity_ratio / (heat_capacity_ratio + 1.0)
    ) * (upstream_mach_number**2 - 1.0)
    if pressure_ratio <= 1.0 or not math.isfinite(pressure_ratio):
        raise NumericalError("Computed a nonphysical static-pressure ratio across a normal shock.")
    return pressure_ratio


def compute_post_shock_total_pressure(
    upstream_total_pressure: float,
    upstream_mach_number: float,
    heat_capacity_ratio: float,
) -> float:
    """Compute downstream total pressure from upstream total pressure across a normal shock."""

    upstream_static_pressure = compute_static_pressure(
        upstream_total_pressure,
        upstream_mach_number,
        heat_capacity_ratio,
    )
    downstream_static_pressure = upstream_static_pressure * compute_normal_shock_static_pressure_ratio(
        upstream_mach_number,
        heat_capacity_ratio,
    )
    downstream_mach_number = compute_normal_shock_downstream_mach(
        upstream_mach_number,
        heat_capacity_ratio,
    )
    downstream_total_pressure = compute_total_pressure(
        downstream_static_pressure,
        downstream_mach_number,
        heat_capacity_ratio,
    )
    if downstream_total_pressure >= upstream_total_pressure:
        raise NumericalError("Normal-shock total-pressure recovery must be lower than the upstream total pressure.")
    return downstream_total_pressure


def assemble_gas_state_from_total_conditions(
    *,
    x_value: float,
    area_value: float,
    mach_number: float,
    total_pressure: float,
    total_temperature: float,
    thermo_provider: ThermoProvider,
) -> GasState:
    """Assemble a local gas state from total conditions and Mach number."""

    if area_value <= 0.0 or not math.isfinite(area_value):
        raise NumericalError("Gas-state assembly requires a positive finite area value.")
    if mach_number <= 0.0 or not math.isfinite(mach_number):
        raise NumericalError("Gas-state assembly requires a positive finite Mach number.")

    heat_capacity_ratio = _extract_heat_capacity_ratio(thermo_provider)
    pressure = compute_static_pressure(
        total_pressure,
        mach_number,
        heat_capacity_ratio,
    )
    temperature = compute_static_temperature(
        total_temperature,
        mach_number,
        heat_capacity_ratio,
    )
    thermo_state = evaluate_thermo_state(
        thermo_provider,
        pressure=pressure,
        temperature=temperature,
    )
    velocity = mach_number * thermo_state.sound_speed

    if (
        thermo_state.density <= 0.0
        or thermo_state.sound_speed <= 0.0
        or velocity <= 0.0
        or not math.isfinite(velocity)
    ):
        raise NumericalError("Gas-state assembly produced a nonphysical local gas state.")

    return GasState(
        x=x_value,
        area=area_value,
        pressure=pressure,
        temperature=temperature,
        density=thermo_state.density,
        velocity=velocity,
        mach_number=mach_number,
        thermo_state=ThermoState(
            pressure=thermo_state.pressure,
            temperature=thermo_state.temperature,
            density=thermo_state.density,
            enthalpy=thermo_state.enthalpy,
            sound_speed=thermo_state.sound_speed,
        ),
    )


def assemble_gas_state(
    *,
    x_value: float,
    area_value: float,
    mach_number: float,
    boundary_state: GasBoundaryConditionState,
    thermo_provider: ThermoProvider,
) -> GasState:
    """Assemble a local gas state from Mach number, boundary state, and thermo queries."""

    return assemble_gas_state_from_total_conditions(
        x_value=x_value,
        area_value=area_value,
        mach_number=mach_number,
        total_pressure=boundary_state.total_pressure,
        total_temperature=boundary_state.total_temperature,
        thermo_provider=thermo_provider,
    )