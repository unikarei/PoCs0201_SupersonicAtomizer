"""Bag-stripping regime breakup model (Pilch & Erdman 1987 inspired).

Physics basis
-------------
Pilch & Erdman (1987) identified five breakup regimes for liquid drops in a
gas stream, classified by the gas Weber number at breakup onset:

  We < 12     Stable (no breakup)
  12 ≤ We < 18    Vibrational breakup
  18 ≤ We < 45    Bag breakup
  45 ≤ We < 351   Stripping / sheet thinning breakup
  We ≥ 351    Catastrophic breakup

In every regime, breakup ultimately produces fragments whose Weber number is
close to the critical value (~12).  The child diameter is therefore:

    d_child = We_crit * σ / (ρ_g * u_rel²)

This is the *stable Weber equilibrium diameter* — the largest drop size that
does not break further under the current local conditions.

This model is cleaner and more physically consistent than the ``weber_critical``
model because:
- The child diameter is derived from local flow conditions, not arbitrary
  reduction factors.
- As slip velocity increases, child diameter decreases automatically.
- The breakup criterion is unchanged: We > We_crit.

Regime identification
---------------------
The ``reason`` field in the returned ``BreakupDecision`` identifies which
breakup regime was active, providing useful diagnostic information.

Reference
---------
Pilch, M. & Erdman, C.A. (1987). Use of breakup time data and velocity
history data to predict the maximum size of stable fragments for acceleration-
induced breakup of a liquid drop. International Journal of Multiphase Flow,
13(6), 741-757.

Units
-----
All inputs and outputs are in SI.
"""

from __future__ import annotations

from dataclasses import dataclass

from supersonic_atomizer.common import ConfigurationError, NumericalError
from supersonic_atomizer.domain import BreakupDecision

from .diagnostics import validate_breakup_decision
from .interfaces import BreakupModel, BreakupModelInputs
from .weber_critical import DEFAULT_SURFACE_TENSION, evaluate_weber_number

# Pilch & Erdman (1987) Weber-number regime boundaries
_WE_VIBRATIONAL_LOWER: float = 12.0
_WE_BAG_LOWER: float = 18.0
_WE_STRIPPING_LOWER: float = 45.0
_WE_CATASTROPHIC_LOWER: float = 351.0


def _identify_regime(weber: float) -> str:
    """Return a human-readable breakup regime label."""
    if weber < _WE_VIBRATIONAL_LOWER:
        return "stable"
    if weber < _WE_BAG_LOWER:
        return "vibrational"
    if weber < _WE_STRIPPING_LOWER:
        return "bag"
    if weber < _WE_CATASTROPHIC_LOWER:
        return "stripping"
    return "catastrophic"


@dataclass(frozen=True, slots=True)
class BagStrippingBreakupModel(BreakupModel):
    """Bag-stripping regime breakup model.

    Child diameter is the stable Weber-equilibrium diameter:

        d_child = critical_weber_number * surface_tension / (ρ_g * u_rel²)

    This ensures that fragments produced by breakup are just below the
    critical Weber number and will not break further under the same conditions.

    Parameters
    ----------
    critical_weber_number : float
        Weber-number threshold above which breakup is triggered (default 12.0).
    surface_tension : float
        Liquid–gas surface tension [Pa·m].  Default is water/air at ~20 °C.
    """

    critical_weber_number: float = 12.0
    surface_tension: float = DEFAULT_SURFACE_TENSION

    def __post_init__(self) -> None:
        if self.critical_weber_number <= 0.0:
            raise ConfigurationError(
                "BagStrippingBreakupModel requires a positive critical Weber number."
            )
        if self.surface_tension <= 0.0:
            raise ConfigurationError(
                "BagStrippingBreakupModel requires a positive surface tension."
            )

    @property
    def model_name(self) -> str:
        """Return the stable configuration-facing name for this model."""
        return "bag_stripping"

    def evaluate(self, inputs: BreakupModelInputs) -> BreakupDecision:
        """Return a structured bag-stripping breakup decision.

        When triggered, the child diameter is the stable Weber-equilibrium
        diameter.  The maximum diameter is updated proportionally unless the
        stable diameter calculation results in a smaller value when applied
        independently to the maximum diameter reference.
        """
        gas = inputs.gas_state
        drop = inputs.droplet_state

        if drop.mean_diameter <= 0.0 or drop.maximum_diameter <= 0.0:
            raise NumericalError("Bag-stripping model requires positive droplet diameters.")

        weber = evaluate_weber_number(
            gas_density=gas.density,
            slip_velocity=drop.slip_velocity,
            reference_diameter=drop.mean_diameter,
            surface_tension=self.surface_tension,
        )

        regime = _identify_regime(weber)

        if weber <= self.critical_weber_number:
            decision = BreakupDecision(
                triggered=False,
                weber_number=weber,
                critical_weber_number=self.critical_weber_number,
                updated_mean_diameter=drop.mean_diameter,
                updated_maximum_diameter=drop.maximum_diameter,
                reason=f"No breakup: We={weber:.3g} ≤ We_crit={self.critical_weber_number:.3g} (regime: {regime}).",
            )
        else:
            # Stable child diameter from local conditions
            slip_sq = drop.slip_velocity ** 2
            if slip_sq < 1.0e-20:
                # Numerically zero slip: cannot compute stable diameter; no breakup
                decision = BreakupDecision(
                    triggered=False,
                    weber_number=weber,
                    critical_weber_number=self.critical_weber_number,
                    updated_mean_diameter=drop.mean_diameter,
                    updated_maximum_diameter=drop.maximum_diameter,
                    reason="No breakup: slip velocity is effectively zero; stable diameter undefined.",
                )
            else:
                d_stable = self.critical_weber_number * self.surface_tension / (gas.density * slip_sq)
                d_stable = max(d_stable, 1.0e-9)   # floor at 1 nm

                # Apply the same stability criterion to the maximum diameter reference
                weber_max = evaluate_weber_number(
                    gas_density=gas.density,
                    slip_velocity=drop.slip_velocity,
                    reference_diameter=drop.maximum_diameter,
                    surface_tension=self.surface_tension,
                )
                if weber_max > self.critical_weber_number:
                    d_stable_max = self.critical_weber_number * self.surface_tension / (gas.density * slip_sq)
                    d_stable_max = max(d_stable_max, d_stable)
                else:
                    d_stable_max = drop.maximum_diameter

                new_mean_d = min(drop.mean_diameter, d_stable)
                new_max_d = max(min(drop.maximum_diameter, d_stable_max), new_mean_d)

                decision = BreakupDecision(
                    triggered=True,
                    weber_number=weber,
                    critical_weber_number=self.critical_weber_number,
                    updated_mean_diameter=new_mean_d,
                    updated_maximum_diameter=new_max_d,
                    reason=(
                        f"Breakup triggered: We={weber:.3g} > We_crit={self.critical_weber_number:.3g} "
                        f"(regime: {regime}); child diameter from stable-Weber equilibrium."
                    ),
                )

        validate_breakup_decision(decision)
        return decision
