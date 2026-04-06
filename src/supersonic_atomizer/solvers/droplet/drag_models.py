"""Drag-model abstractions and the MVP standard-sphere implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import math

from supersonic_atomizer.common import ConfigurationError


@dataclass(frozen=True, slots=True)
class StandardSphereDragInputs:
    """Structured inputs for the MVP standard-sphere drag evaluation."""

    gas_density: float
    slip_velocity: float
    droplet_diameter: float
    dynamic_viscosity: float = 1.8e-5


@dataclass(frozen=True, slots=True)
class DragEvaluation:
    """Structured drag evaluation output for droplet transport updates."""

    reynolds_number: float
    drag_coefficient: float
    acceleration: float


class DragModel(ABC):
    """Abstract drag-model boundary used by the droplet transport solver."""

    @abstractmethod
    def evaluate(self, inputs: StandardSphereDragInputs) -> DragEvaluation:
        """Evaluate drag response from local gas and droplet transport inputs."""


@dataclass(frozen=True, slots=True)
class StandardSphereDragModel(DragModel):
    """MVP drag model using a simple standard-sphere correlation."""

    droplet_density: float = 1000.0

    def evaluate(self, inputs: StandardSphereDragInputs) -> DragEvaluation:
        if inputs.gas_density <= 0.0 or not math.isfinite(inputs.gas_density):
            raise ConfigurationError("Standard-sphere drag requires a positive finite gas density.")
        if inputs.droplet_diameter <= 0.0 or not math.isfinite(inputs.droplet_diameter):
            raise ConfigurationError("Standard-sphere drag requires a positive finite droplet diameter.")
        if inputs.dynamic_viscosity <= 0.0 or not math.isfinite(inputs.dynamic_viscosity):
            raise ConfigurationError("Standard-sphere drag requires a positive finite dynamic viscosity.")
        if self.droplet_density <= 0.0 or not math.isfinite(self.droplet_density):
            raise ConfigurationError("Standard-sphere drag requires a positive finite droplet density.")

        slip_magnitude = abs(inputs.slip_velocity)
        if slip_magnitude == 0.0:
            return DragEvaluation(reynolds_number=0.0, drag_coefficient=0.0, acceleration=0.0)

        reynolds_number = (
            inputs.gas_density
            * slip_magnitude
            * inputs.droplet_diameter
            / inputs.dynamic_viscosity
        )

        if reynolds_number <= 0.0 or not math.isfinite(reynolds_number):
            raise ConfigurationError("Standard-sphere drag produced an invalid Reynolds number.")

        drag_coefficient = (24.0 / reynolds_number) * (1.0 + 0.15 * reynolds_number**0.687)
        acceleration = (
            3.0
            * drag_coefficient
            * inputs.gas_density
            * slip_magnitude
            * inputs.slip_velocity
            / (4.0 * self.droplet_density * inputs.droplet_diameter)
        )

        return DragEvaluation(
            reynolds_number=reynolds_number,
            drag_coefficient=drag_coefficient,
            acceleration=acceleration,
        )