"""MVP Weber-threshold breakup model and Weber-number helper."""

from __future__ import annotations

from dataclasses import dataclass

from supersonic_atomizer.common import ConfigurationError, NumericalError
from supersonic_atomizer.domain import BreakupDecision

from .diagnostics import validate_breakup_decision
from .interfaces import BreakupModel, BreakupModelInputs

DEFAULT_SURFACE_TENSION = 0.072


def evaluate_weber_number(
    *,
    gas_density: float,
    slip_velocity: float,
    reference_diameter: float,
    surface_tension: float = DEFAULT_SURFACE_TENSION,
) -> float:
    """Evaluate the MVP Weber number using SI-consistent inputs."""

    if gas_density <= 0.0:
        raise NumericalError("Weber-number evaluation requires a positive gas density.")
    if reference_diameter <= 0.0:
        raise NumericalError("Weber-number evaluation requires a positive reference diameter.")
    if surface_tension <= 0.0:
        raise NumericalError("Weber-number evaluation requires a positive surface tension.")
    return gas_density * slip_velocity**2 * reference_diameter / surface_tension


@dataclass(frozen=True, slots=True)
class CriticalWeberBreakupModel(BreakupModel):
    """Executable MVP breakup model using a critical Weber-number threshold."""

    critical_weber_number: float
    breakup_factor_mean: float
    breakup_factor_max: float
    surface_tension: float = DEFAULT_SURFACE_TENSION

    def __post_init__(self) -> None:
        if self.critical_weber_number <= 0.0:
            raise ConfigurationError("The Weber-critical breakup model requires a positive critical Weber number.")
        if self.surface_tension <= 0.0:
            raise ConfigurationError("The Weber-critical breakup model requires a positive surface tension.")
        if not 0.0 < self.breakup_factor_mean < 1.0:
            raise ConfigurationError(
                "The Weber-critical breakup model requires breakup_factor_mean to be greater than 0 and less than 1."
            )
        if not 0.0 < self.breakup_factor_max < 1.0:
            raise ConfigurationError(
                "The Weber-critical breakup model requires breakup_factor_max to be greater than 0 and less than 1."
            )

    @property
    def model_name(self) -> str:
        """Return the stable configuration-facing name for this breakup model."""

        return "weber_critical"

    def evaluate(self, inputs: BreakupModelInputs) -> BreakupDecision:
        """Return the structured Weber-threshold breakup decision."""

        weber_number = evaluate_weber_number(
            gas_density=inputs.gas_state.density,
            slip_velocity=inputs.droplet_state.slip_velocity,
            reference_diameter=inputs.droplet_state.mean_diameter,
            surface_tension=self.surface_tension,
        )

        if weber_number > self.critical_weber_number:
            updated_mean_diameter = inputs.droplet_state.mean_diameter * self.breakup_factor_mean
            updated_maximum_diameter = max(
                inputs.droplet_state.maximum_diameter * self.breakup_factor_max,
                updated_mean_diameter,
            )
            decision = BreakupDecision(
                triggered=True,
                weber_number=weber_number,
                critical_weber_number=self.critical_weber_number,
                updated_mean_diameter=updated_mean_diameter,
                updated_maximum_diameter=updated_maximum_diameter,
                reason="Breakup triggered: Weber number exceeded the configured critical threshold.",
            )
        else:
            decision = BreakupDecision(
                triggered=False,
                weber_number=weber_number,
                critical_weber_number=self.critical_weber_number,
                updated_mean_diameter=inputs.droplet_state.mean_diameter,
                updated_maximum_diameter=inputs.droplet_state.maximum_diameter,
                reason="No breakup: Weber number did not exceed the configured critical threshold.",
            )

        validate_breakup_decision(decision)
        return decision