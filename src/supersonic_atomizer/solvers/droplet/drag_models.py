"""Drag-model abstractions and runtime drag-model selection helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import math

from supersonic_atomizer.common import ConfigurationError, ModelSelectionError
from supersonic_atomizer.domain import ModelSelectionConfig


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


def _validate_drag_inputs(inputs: StandardSphereDragInputs, droplet_density: float) -> None:
    if inputs.gas_density <= 0.0 or not math.isfinite(inputs.gas_density):
        raise ConfigurationError("Drag evaluation requires a positive finite gas density.")
    if inputs.droplet_diameter <= 0.0 or not math.isfinite(inputs.droplet_diameter):
        raise ConfigurationError("Drag evaluation requires a positive finite droplet diameter.")
    if inputs.dynamic_viscosity <= 0.0 or not math.isfinite(inputs.dynamic_viscosity):
        raise ConfigurationError("Drag evaluation requires a positive finite dynamic viscosity.")
    if droplet_density <= 0.0 or not math.isfinite(droplet_density):
        raise ConfigurationError("Drag evaluation requires a positive finite droplet density.")


def _compute_reynolds_number(inputs: StandardSphereDragInputs) -> float:
    slip_magnitude = abs(inputs.slip_velocity)
    if slip_magnitude == 0.0:
        return 0.0

    reynolds_number = (
        inputs.gas_density
        * slip_magnitude
        * inputs.droplet_diameter
        / inputs.dynamic_viscosity
    )
    if reynolds_number <= 0.0 or not math.isfinite(reynolds_number):
        raise ConfigurationError("Drag evaluation produced an invalid Reynolds number.")
    return reynolds_number


def _compute_standard_sphere_drag_coefficient(reynolds_number: float) -> float:
    if reynolds_number <= 0.0 or not math.isfinite(reynolds_number):
        raise ConfigurationError("Standard-sphere drag coefficient requires a positive finite Reynolds number.")
    if reynolds_number < 1.0:
        return 24.0 / reynolds_number
    if reynolds_number <= 1000.0:
        return (24.0 / reynolds_number) * (1.0 + 0.15 * reynolds_number**0.687)
    return 0.44


def _compute_drag_acceleration(
    *,
    drag_coefficient: float,
    gas_density: float,
    slip_velocity: float,
    droplet_density: float,
    droplet_diameter: float,
) -> float:
    return (
        3.0
        * drag_coefficient
        * gas_density
        * abs(slip_velocity)
        * slip_velocity
        / (4.0 * droplet_density * droplet_diameter)
    )


@dataclass(frozen=True, slots=True)
class StandardSphereDragModel(DragModel):
    """Standard-sphere drag model with broad Reynolds-number coverage."""

    droplet_density: float = 998.2

    def evaluate(self, inputs: StandardSphereDragInputs) -> DragEvaluation:
        _validate_drag_inputs(inputs, self.droplet_density)
        reynolds_number = _compute_reynolds_number(inputs)
        if reynolds_number == 0.0:
            return DragEvaluation(reynolds_number=0.0, drag_coefficient=0.0, acceleration=0.0)

        drag_coefficient = _compute_standard_sphere_drag_coefficient(reynolds_number)
        acceleration = _compute_drag_acceleration(
            drag_coefficient=drag_coefficient,
            gas_density=inputs.gas_density,
            slip_velocity=inputs.slip_velocity,
            droplet_density=self.droplet_density,
            droplet_diameter=inputs.droplet_diameter,
        )

        return DragEvaluation(
            reynolds_number=reynolds_number,
            drag_coefficient=drag_coefficient,
            acceleration=acceleration,
        )


@dataclass(frozen=True, slots=True)
class NonSphericalSphereDragModel(DragModel):
    """Haider-Levenspiel non-spherical drag correlation."""

    droplet_density: float = 998.2
    sphericity: float = 0.85

    def __post_init__(self) -> None:
        if self.sphericity <= 0.0 or self.sphericity > 1.0 or not math.isfinite(self.sphericity):
            raise ConfigurationError(
                "Non-spherical drag requires sphericity to be greater than 0 and less than or equal to 1."
            )

    def evaluate(self, inputs: StandardSphereDragInputs) -> DragEvaluation:
        _validate_drag_inputs(inputs, self.droplet_density)
        reynolds_number = _compute_reynolds_number(inputs)
        if reynolds_number == 0.0:
            return DragEvaluation(reynolds_number=0.0, drag_coefficient=0.0, acceleration=0.0)

        phi = self.sphericity
        coefficient_a = math.exp(2.3288 - 6.4581 * phi + 2.4486 * phi**2)
        coefficient_b = 0.0964 + 0.5565 * phi
        coefficient_c = math.exp(4.905 - 13.8944 * phi + 18.4222 * phi**2 - 10.2599 * phi**3)
        coefficient_d = math.exp(1.4681 + 12.2584 * phi - 20.7322 * phi**2 + 15.8855 * phi**3)
        drag_coefficient = (
            24.0 / reynolds_number * (1.0 + coefficient_a * reynolds_number**coefficient_b)
            + coefficient_c / (1.0 + coefficient_d / reynolds_number)
        )
        acceleration = _compute_drag_acceleration(
            drag_coefficient=drag_coefficient,
            gas_density=inputs.gas_density,
            slip_velocity=inputs.slip_velocity,
            droplet_density=self.droplet_density,
            droplet_diameter=inputs.droplet_diameter,
        )
        return DragEvaluation(
            reynolds_number=reynolds_number,
            drag_coefficient=drag_coefficient,
            acceleration=acceleration,
        )


def select_drag_model(model_selection: ModelSelectionConfig) -> DragModel:
    """Resolve the configured runtime drag model without silent fallbacks."""

    if model_selection.drag_model == "standard_sphere":
        return StandardSphereDragModel(droplet_density=model_selection.droplet_density)
    if model_selection.drag_model == "nonspherical_sphere":
        return NonSphericalSphereDragModel(
            droplet_density=model_selection.droplet_density,
            sphericity=model_selection.droplet_sphericity,
        )
    raise ModelSelectionError(
        f"Unsupported drag model '{model_selection.drag_model}'. Supported models: standard_sphere, nonspherical_sphere."
    )