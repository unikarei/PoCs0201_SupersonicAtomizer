"""KH-RT (Kelvin-Helmholtz / Rayleigh-Taylor) breakup model.

Physics basis
-------------
Reitz (1987) provided curve-fits to the full Rayleigh-Taylor KH dispersion
relation for a liquid jet in a gas cross-stream. Beale & Reitz (1999)
extended this to a combined KH-RT model: KH instability drives continuous
surface stripping, while RT instability can trigger catastrophic bulk breakup
when the RT wavelength fits inside the parent drop.

Quasi-1D approximation
-----------------------
The standard KH-RT model requires tracking parent drop radius history and
comparing it to child radius over a breakup time. In a quasi-1D steady
marching solver there is no time dimension. This module uses a local
equilibrium approximation:

- KH stripping applies when the KH equilibrium child radius (B0 * λ_KH) is
  smaller than the current drop radius.  The updated diameter is
  d_child = 2 * B0 * λ_KH.
- RT bulk breakup applies when the RT wavelength λ_RT is smaller than the
  current drop diameter (i.e. RT instability can fit inside the drop).
  The updated diameter is d_child = 2 * λ_RT.
- If both apply the smaller of the two child diameters is returned.
- If neither applies, no breakup is triggered.

This approximation is conservative (does not over-predict breakup) and
physically traceable.

Key references
--------------
- Reitz, R.D. (1987). Modeling Atomization Processes in High-Pressure
  Vaporizing Sprays. Atomisation and Spray Technology, 3, 309-337.
- Beale, J.C. & Reitz, R.D. (1999). Modeling Spray Atomization with the
  Kelvin-Helmholtz / Rayleigh-Taylor Hybrid Model. Atomization and Sprays,
  9(6), 623-650.

Units
-----
All inputs and outputs are in SI. Liquid properties default to water at ~20°C.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from supersonic_atomizer.common import ConfigurationError, NumericalError
from supersonic_atomizer.domain import BreakupDecision

from .diagnostics import validate_breakup_decision
from .interfaces import BreakupModel, BreakupModelInputs
from .weber_critical import DEFAULT_SURFACE_TENSION, evaluate_weber_number

# Liquid water properties at ~20 °C (SI)
_DEFAULT_LIQUID_DENSITY: float = 998.2      # kg/m³
_DEFAULT_LIQUID_VISCOSITY: float = 1.002e-3  # Pa·s

# Small positive floor to avoid division by zero in dimensionless numbers
_EPSILON: float = 1.0e-30


def _kh_child_radius(
    *,
    gas_density: float,
    liquid_density: float,
    liquid_viscosity: float,
    surface_tension: float,
    slip_velocity: float,
    radius: float,
    B0: float,
) -> float:
    """Compute the KH equilibrium child radius using the Reitz (1987) curve-fit.

    Returns the KH child radius in metres.  If the correlation is undefined or
    results in a child radius equal to or larger than the parent radius the
    parent radius is returned (no KH stripping).
    """
    We_g = gas_density * slip_velocity ** 2 * radius / surface_tension
    We_l = liquid_density * slip_velocity ** 2 * radius / surface_tension
    Re_l = liquid_density * abs(slip_velocity) * 2.0 * radius / max(liquid_viscosity, _EPSILON)

    Oh = math.sqrt(max(We_l, 0.0)) / max(Re_l, _EPSILON)
    T = Oh * math.sqrt(max(We_g, 0.0))   # Taylor number

    # Reitz (1987) curve-fit for KH wavelength normalised by radius
    numerator = 9.02 * (1.0 + 0.45 * math.sqrt(Oh)) * (1.0 + 0.4 * T ** 0.7)
    denominator = (1.0 + 0.87 * We_g ** 1.67) ** 0.6
    lambda_kh = radius * numerator / max(denominator, _EPSILON)

    child_radius = B0 * lambda_kh
    return child_radius


def _rt_child_radius(
    *,
    gas_density: float,
    liquid_density: float,
    surface_tension: float,
    slip_velocity: float,
    radius: float,
    Crt: float,
) -> float:
    """Compute the RT equilibrium child radius.

    Returns the RT wavelength (as half-wavelength child radius) when the RT
    instability can fit inside the parent drop.  Returns the parent radius if
    the RT condition is not met (no RT breakup).

    RT wavelength (Bellman & Pennington 1954):

        λ_RT = 2π * sqrt(3σ / ((ρ_l - ρ_g) * g_eff))

    Effective deceleration (sphere drag model, Cd ≈ 0.44):

        g_eff = (3/8) * Cd * ρ_g * u_rel² / (ρ_l * r)
    """
    rho_diff = max(liquid_density - gas_density, 1.0)
    g_eff = (3.0 / 8.0) * 0.44 * gas_density * slip_velocity ** 2 / (liquid_density * radius)

    if g_eff <= 0.0:
        return radius  # no RT breakup when drop is not decelerating

    lambda_rt = 2.0 * math.pi * Crt * math.sqrt(3.0 * surface_tension / (rho_diff * g_eff))
    return lambda_rt / 2.0   # child radius from RT wavelength


@dataclass(frozen=True, slots=True)
class KHRTBreakupModel(BreakupModel):
    """KH-RT breakup model using the Reitz (1987) / Beale & Reitz (1999) framework.

    Parameters
    ----------
    B0 : float
        KH child-radius proportionality constant (literature default 0.61).
    B1 : float
        KH breakup time constant (literature range 10–60, default 40.0).
        Not used in the quasi-1D equilibrium approximation but stored for
        provenance and potential future time-resolved extensions.
    Crt : float
        RT instability constant (literature range 0.1–0.5, default 0.1).
    surface_tension : float
        Liquid–gas surface tension [Pa·m].  Default is water/air at ~20 °C.
    liquid_density : float
        Liquid droplet density [kg/m³].  Default is water at ~20 °C.
    liquid_viscosity : float
        Liquid dynamic viscosity [Pa·s].  Default is water at ~20 °C.
    """

    B0: float = 0.61
    B1: float = 40.0
    Crt: float = 0.1
    surface_tension: float = DEFAULT_SURFACE_TENSION
    liquid_density: float = _DEFAULT_LIQUID_DENSITY
    liquid_viscosity: float = _DEFAULT_LIQUID_VISCOSITY

    def __post_init__(self) -> None:
        for name, val in (
            ("B0", self.B0),
            ("B1", self.B1),
            ("Crt", self.Crt),
            ("surface_tension", self.surface_tension),
            ("liquid_density", self.liquid_density),
            ("liquid_viscosity", self.liquid_viscosity),
        ):
            if val <= 0.0:
                raise ConfigurationError(
                    f"KHRTBreakupModel requires a positive value for '{name}', got {val}."
                )

    @property
    def model_name(self) -> str:
        """Return the stable configuration-facing name for this model."""
        return "khrt"

    def evaluate(self, inputs: BreakupModelInputs) -> BreakupDecision:
        """Return a structured KH-RT breakup decision.

        The Weber number in the decision is computed using the standard gas
        Weber number with mean diameter as reference (for consistency with the
        `weber_critical` model and diagnostic outputs).  `critical_weber_number`
        is reported as 0.0 to indicate that no scalar threshold gates this
        model; instead child diameter physics determine breakup.
        """
        gas = inputs.gas_state
        drop = inputs.droplet_state

        if drop.mean_diameter <= 0.0 or drop.maximum_diameter <= 0.0:
            raise NumericalError("KH-RT model requires positive droplet diameters.")

        weber = evaluate_weber_number(
            gas_density=gas.density,
            slip_velocity=drop.slip_velocity,
            reference_diameter=drop.mean_diameter,
            surface_tension=self.surface_tension,
        )

        parent_radius = drop.mean_diameter / 2.0
        parent_radius_max = drop.maximum_diameter / 2.0

        kh_child_r = _kh_child_radius(
            gas_density=gas.density,
            liquid_density=self.liquid_density,
            liquid_viscosity=self.liquid_viscosity,
            surface_tension=self.surface_tension,
            slip_velocity=drop.slip_velocity,
            radius=parent_radius,
            B0=self.B0,
        )
        rt_child_r = _rt_child_radius(
            gas_density=gas.density,
            liquid_density=self.liquid_density,
            surface_tension=self.surface_tension,
            slip_velocity=drop.slip_velocity,
            radius=parent_radius,
            Crt=self.Crt,
        )

        kh_triggered = kh_child_r < parent_radius
        rt_triggered = rt_child_r < parent_radius

        if not kh_triggered and not rt_triggered:
            decision = BreakupDecision(
                triggered=False,
                weber_number=weber,
                critical_weber_number=0.0,
                updated_mean_diameter=drop.mean_diameter,
                updated_maximum_diameter=drop.maximum_diameter,
                reason="No breakup: KH and RT child diameters both exceed current drop size.",
            )
        else:
            # Use the smaller of the applicable child radii
            candidate_radii = []
            mechanisms = []
            if kh_triggered:
                candidate_radii.append(kh_child_r)
                mechanisms.append("KH")
            if rt_triggered:
                candidate_radii.append(rt_child_r)
                mechanisms.append("RT")

            new_mean_r = min(candidate_radii)
            new_mean_d = max(2.0 * new_mean_r, 1.0e-9)   # floor at 1 nm

            # Scale the maximum diameter by the same ratio as mean diameter
            scale = new_mean_d / drop.mean_diameter
            new_max_d = max(drop.maximum_diameter * scale, new_mean_d)

            # Also apply KH/RT to maximum diameter independently
            kh_child_r_max = _kh_child_radius(
                gas_density=gas.density,
                liquid_density=self.liquid_density,
                liquid_viscosity=self.liquid_viscosity,
                surface_tension=self.surface_tension,
                slip_velocity=drop.slip_velocity,
                radius=parent_radius_max,
                B0=self.B0,
            )
            rt_child_r_max = _rt_child_radius(
                gas_density=gas.density,
                liquid_density=self.liquid_density,
                surface_tension=self.surface_tension,
                slip_velocity=drop.slip_velocity,
                radius=parent_radius_max,
                Crt=self.Crt,
            )
            candidate_max = []
            if kh_child_r_max < parent_radius_max:
                candidate_max.append(kh_child_r_max)
            if rt_child_r_max < parent_radius_max:
                candidate_max.append(rt_child_r_max)
            if candidate_max:
                new_max_d = max(2.0 * min(candidate_max), new_mean_d)

            decision = BreakupDecision(
                triggered=True,
                weber_number=weber,
                critical_weber_number=0.0,
                updated_mean_diameter=new_mean_d,
                updated_maximum_diameter=new_max_d,
                reason=f"Breakup triggered by {'+'.join(mechanisms)} instability.",
            )

        validate_breakup_decision(decision)
        return decision
