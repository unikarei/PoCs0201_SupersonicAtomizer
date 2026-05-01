"""Primary-breakup coordinator utilities for liquid-jet injection mode.

This module provides a small empirical correlation-based coordinator that
estimates a primary-breakup length `L_primary_breakup` and generates an
initial droplet SMD (mean, max) to hand over to the droplet transport layer.

The implementations are intentionally simple and tunable via a coefficient
to remain empirical for the MVP.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from supersonic_atomizer.breakup.weber_critical import evaluate_weber_number
from supersonic_atomizer.domain import DropletInjectionConfig, GasState


@dataclass(frozen=True, slots=True)
class PrimaryBreakupResult:
    L_primary_breakup: float
    generated_mean_diameter: float
    generated_maximum_diameter: float
    weber_at_breakup: float


def estimate_primary_breakup(
    *,
    liquid_diameter: float,
    liquid_velocity: float,
    gas_state: GasState,
    surface_tension: float,
    liquid_density: float,
    primary_coeff: float = 10.0,
) -> PrimaryBreakupResult:
    """Estimate a primary-breakup length and generated droplet sizes.

    A minimal empirical correlation is used for the MVP:
        L = C * d_j * sqrt(We_g)
    where We_g = rho_g * U_rel^2 * d_j / sigma.

    The generated mean droplet diameter is set to a fixed fraction of the jet
    diameter (configurable in future revisions); defaults are conservative.
    """
    if liquid_diameter <= 0.0:
        raise ValueError("liquid_diameter must be positive")
    if liquid_velocity <= 0.0:
        raise ValueError("liquid_velocity must be positive")
    if surface_tension <= 0.0:
        raise ValueError("surface_tension must be positive")

    # Relative velocity between gas and liquid jet
    U_rel = abs(gas_state.velocity - liquid_velocity)
    we_g = evaluate_weber_number(
        gas_density=gas_state.density,
        slip_velocity=U_rel,
        reference_diameter=liquid_diameter,
        surface_tension=surface_tension,
    )

    L = primary_coeff * liquid_diameter * math.sqrt(max(we_g, 1.0))

    # Generated droplet sizing (simple fraction of jet diameter)
    mean_fraction = 0.2
    max_fraction = 0.5
    generated_mean = liquid_diameter * mean_fraction
    generated_max = liquid_diameter * max_fraction

    return PrimaryBreakupResult(
        L_primary_breakup=L,
        generated_mean_diameter=generated_mean,
        generated_maximum_diameter=generated_max,
        weber_at_breakup=we_g,
    )


def estimate_from_config(*, injection_config: DropletInjectionConfig, gas_state: GasState) -> PrimaryBreakupResult:
    coeff = injection_config.primary_breakup_coefficient or 10.0
    return estimate_primary_breakup(
        liquid_diameter=injection_config.liquid_jet_diameter,
        liquid_velocity=injection_config.liquid_velocity,
        gas_state=gas_state,
        surface_tension=injection_config.surface_tension or 0.072,
        liquid_density=injection_config.liquid_density or 998.2,
        primary_coeff=coeff,
    )
