"""Taylor Analogy Breakup (TAB) model - lightweight placeholder implementation.

This file implements a simple TAB-style breakup model that conforms to
the `BreakupModel` interface. It uses a local, time-agnostic approximation:
- if local Weber number exceeds a configurable critical value, the model
  reduces droplet diameters by a tunable fraction and reports a triggered
  breakup. This is intentionally conservative and designed as a safe
  integration scaffold; a physics-accurate TAB requires internal state and
  explicit time-integration which can be added later.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp
from typing import Optional

from supersonic_atomizer.breakup.interfaces import BreakupModel, BreakupModelInputs
from supersonic_atomizer.domain.state_models import BreakupDecision


@dataclass(frozen=True)
class TABConfig:
    # TAB mechanical parameters (user-tunable)
    spring_k: float = 1.0e-3  # N/m (placeholder default)
    damping_c: float = 1.0e-6  # kg/s (placeholder default)
    breakup_threshold: float = 1.0  # nondimensional deformation threshold
    reduction_fraction: float = 0.5  # diameter multiplier when breakup occurs


class TABBreakupModel(BreakupModel):
    """A simple time-integrated TAB approximation.

    This implementation approximates a forced damped oscillator response
    to a quasi-steady aerodynamic forcing over the local interaction time
    `dt`. It does not maintain internal oscillator state between spatial
    steps; instead it assumes the oscillator starts from rest at each
    evaluated segment (conservative for breakup triggering). The model is
    intentionally simple but captures a time-scale-dependent response.
    """

    def __init__(
        self,
        *,
        spring_k: float = 1.0e-3,
        damping_c: float = 1.0e-6,
        breakup_threshold: float = 1.0,
        reduction_fraction: float = 0.5,
    ) -> None:
        self._cfg = TABConfig(spring_k, damping_c, breakup_threshold, reduction_fraction)

    @property
    def model_name(self) -> str:
        return "tab"

    def evaluate(self, inputs: BreakupModelInputs) -> BreakupDecision:
        d_state = inputs.droplet_state
        g_state = inputs.gas_state
        dt = inputs.dt if inputs.dt is not None else 0.0

        # Local properties
        rho_g = float(g_state.thermo_state.density)
        rho_l = float(self._estimate_liquid_density(d_state))
        d = float(d_state.mean_diameter)
        u_rel = float(d_state.slip_velocity)

        # Simple aerodynamic forcing scale ~ 0.5 * rho_g * u_rel^2 * area_scale
        area_scale = max(d * d, 1.0e-20)
        F = 0.5 * rho_g * (u_rel ** 2) * area_scale

        # Mechanical parameters
        k = float(self._cfg.spring_k)
        c = float(self._cfg.damping_c)

        # Effective mass scale (order of droplet mass)
        m = max((3.14159 / 6.0) * rho_l * (d ** 3), 1.0e-30)

        # Steady-state deformation under constant forcing: X_inf = F / k
        X_inf = F / max(k, 1.0e-30)

        # Approximate transient approach rate alpha ~ c/m
        alpha = c / m if m > 0 else 1.0

        # Simple first-order approach to steady-state over dt: X(dt) = X_inf * (1 - exp(-alpha * dt))
        X_dt = X_inf * (1.0 - exp(-alpha * dt))

        triggered = X_dt >= float(self._cfg.breakup_threshold)

        if not triggered:
            return BreakupDecision(
                triggered=False,
                weber_number=float(d_state.weber_number),
                critical_weber_number=float(self._cfg.breakup_threshold),
                updated_mean_diameter=d_state.mean_diameter,
                updated_maximum_diameter=d_state.maximum_diameter,
                reason="tab_not_triggered",
            )

        # On trigger, reduce diameters conservatively
        red = float(self._cfg.reduction_fraction)
        new_mean = max(1.0e-12, d_state.mean_diameter * red)
        new_max = max(new_mean, d_state.maximum_diameter * red)

        return BreakupDecision(
            triggered=True,
            weber_number=float(d_state.weber_number),
            critical_weber_number=float(self._cfg.breakup_threshold),
            updated_mean_diameter=new_mean,
            updated_maximum_diameter=new_max,
            reason="tab_time_integrated_trigger",
        )

    def _estimate_liquid_density(self, d_state: object) -> float:
        # Use droplet density where available via config; fallback to 998.2
        try:
            # droplet density may be accessible via surrounding models; default fallback
            return float(getattr(d_state, "liquid_density", 998.2))
        except Exception:
            return 998.2
