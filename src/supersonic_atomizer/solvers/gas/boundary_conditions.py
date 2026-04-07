"""Gas-side boundary-condition initialization for supported foundation cases."""

from __future__ import annotations

from dataclasses import dataclass
import math

from supersonic_atomizer.common import ConfigurationError, NumericalError, ThermoError
from supersonic_atomizer.domain import BoundaryConditionConfig
from supersonic_atomizer.thermo.interfaces import ThermoProvider


def _extract_heat_capacity_ratio(thermo_provider: ThermoProvider) -> float:
    gamma = getattr(thermo_provider, "heat_capacity_ratio", None)
    if not isinstance(gamma, (int, float)) or gamma <= 1.0:
        raise ThermoError(
            "The supported gas-solver foundation path requires a thermo provider "
            "with a valid 'heat_capacity_ratio' attribute."
        )
    return float(gamma)


def _compute_critical_pressure_ratio(heat_capacity_ratio: float) -> float:
    return (2.0 / (heat_capacity_ratio + 1.0)) ** (
        heat_capacity_ratio / (heat_capacity_ratio - 1.0)
    )


@dataclass(frozen=True, slots=True)
class GasBoundaryConditionState:
    """Derived gas-side boundary state for the current quasi-1D gas runtime path."""

    total_pressure: float
    total_temperature: float
    outlet_static_pressure: float
    outlet_pressure_ratio: float
    outlet_mach_number: float


def initialize_gas_boundary_conditions(
    boundary_conditions: BoundaryConditionConfig,
    thermo_provider: ThermoProvider,
) -> GasBoundaryConditionState:
    """Initialize supported gas-side boundary values from validated runtime inputs."""

    if boundary_conditions.Pt_in <= 0.0:
        raise ConfigurationError("Gas boundary initialization requires positive inlet total pressure.")
    if boundary_conditions.Tt_in <= 0.0:
        raise ConfigurationError("Gas boundary initialization requires positive inlet total temperature.")
    if boundary_conditions.Ps_out <= 0.0:
        raise ConfigurationError("Gas boundary initialization requires positive outlet static pressure.")
    if boundary_conditions.Pt_in <= boundary_conditions.Ps_out:
        raise ConfigurationError(
            "Supported gas boundary initialization requires Pt_in to be greater than Ps_out."
        )

    gamma = _extract_heat_capacity_ratio(thermo_provider)
    outlet_pressure_ratio = boundary_conditions.Ps_out / boundary_conditions.Pt_in
    critical_pressure_ratio = _compute_critical_pressure_ratio(gamma)
    if outlet_pressure_ratio <= critical_pressure_ratio:
        outlet_mach_number = 1.0
    else:
        outlet_mach_number = math.sqrt(
            (2.0 / (gamma - 1.0))
            * ((1.0 / outlet_pressure_ratio) ** ((gamma - 1.0) / gamma) - 1.0)
        )

    if outlet_mach_number <= 0.0 or not math.isfinite(outlet_mach_number):
        raise NumericalError(
            "Failed gas boundary closure: derived outlet Mach number is nonphysical for the supplied pressure ratio."
        )

    return GasBoundaryConditionState(
        total_pressure=boundary_conditions.Pt_in,
        total_temperature=boundary_conditions.Tt_in,
        outlet_static_pressure=boundary_conditions.Ps_out,
        outlet_pressure_ratio=outlet_pressure_ratio,
        outlet_mach_number=outlet_mach_number,
    )