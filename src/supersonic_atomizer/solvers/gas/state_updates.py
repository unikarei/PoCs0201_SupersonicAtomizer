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
    """Compute the standard quasi-1D area-to-throat ratio for a subsonic Mach number."""

    if not (0.0 < mach_number < 1.0):
        raise NumericalError("Area-Mach relation requires a subsonic Mach number in the open interval (0, 1).")

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


def assemble_gas_state(
    *,
    x_value: float,
    area_value: float,
    mach_number: float,
    boundary_state: GasBoundaryConditionState,
    thermo_provider: ThermoProvider,
) -> GasState:
    """Assemble a local gas state from Mach number, boundary state, and thermo queries."""

    if area_value <= 0.0 or not math.isfinite(area_value):
        raise NumericalError("Gas-state assembly requires a positive finite area value.")
    if not (0.0 < mach_number < 1.0):
        raise NumericalError("Gas-state assembly requires a subsonic Mach number in the open interval (0, 1).")

    heat_capacity_ratio = _extract_heat_capacity_ratio(thermo_provider)
    pressure = compute_static_pressure(
        boundary_state.total_pressure,
        mach_number,
        heat_capacity_ratio,
    )
    temperature = compute_static_temperature(
        boundary_state.total_temperature,
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