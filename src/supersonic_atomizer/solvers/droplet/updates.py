"""Droplet initialization and local transport-update helpers."""

from __future__ import annotations

import math

from supersonic_atomizer.common import NumericalError
from supersonic_atomizer.breakup import evaluate_weber_number
from supersonic_atomizer.domain import DropletInjectionConfig, DropletState, GasState
from supersonic_atomizer.solvers.droplet.diagnostics import validate_droplet_state
from supersonic_atomizer.solvers.droplet.drag_models import (
    DragModel,
    StandardSphereDragInputs,
)

WATER_SURFACE_TENSION = 0.072


def compute_distribution_moments(
    *,
    mean_diameter: float,
    maximum_diameter: float,
    distribution_model: str,
    distribution_sigma: float,
) -> tuple[float, float]:
    """Return SMD and standard deviation for the configured distribution model."""

    if distribution_model == "mono":
        return mean_diameter, 0.0

    baseline_spread = max((maximum_diameter - mean_diameter) / 3.0, 0.0)
    model_spread = max(distribution_sigma * mean_diameter, baseline_spread)
    coefficient_of_variation = model_spread / max(mean_diameter, 1.0e-12)
    smd_diameter = mean_diameter * (1.0 + coefficient_of_variation * coefficient_of_variation)
    return smd_diameter, model_spread


def compute_weber_number(*, gas_density: float, slip_velocity: float, droplet_diameter: float) -> float:
    """Compute the droplet Weber number using the MVP surface-tension constant."""

    return evaluate_weber_number(
        gas_density=gas_density,
        slip_velocity=slip_velocity,
        reference_diameter=droplet_diameter,
        surface_tension=WATER_SURFACE_TENSION,
    )


def initialize_droplet_state(
    *,
    gas_state: GasState,
    injection_config: DropletInjectionConfig,
    drag_model: DragModel,
    distribution_model: str = "mono",
    distribution_sigma: float = 0.35,
) -> DropletState:
    """Initialize the inlet-side representative droplet state from validated inputs."""

    slip_velocity = gas_state.velocity - injection_config.droplet_velocity_in
    drag_evaluation = drag_model.evaluate(
        StandardSphereDragInputs(
            gas_density=gas_state.density,
            slip_velocity=slip_velocity,
            droplet_diameter=injection_config.droplet_diameter_mean_in,
            dynamic_viscosity=gas_state.thermo_state.dynamic_viscosity or 1.8e-5,
        )
    )
    smd_diameter, diameter_stddev = compute_distribution_moments(
        mean_diameter=injection_config.droplet_diameter_mean_in,
        maximum_diameter=injection_config.droplet_diameter_max_in,
        distribution_model=distribution_model,
        distribution_sigma=distribution_sigma,
    )

    droplet_state = DropletState(
        x=gas_state.x,
        velocity=injection_config.droplet_velocity_in,
        slip_velocity=slip_velocity,
        mean_diameter=injection_config.droplet_diameter_mean_in,
        maximum_diameter=injection_config.droplet_diameter_max_in,
        weber_number=compute_weber_number(
            gas_density=gas_state.density,
            slip_velocity=slip_velocity,
            droplet_diameter=injection_config.droplet_diameter_mean_in,
        ),
        smd_diameter=smd_diameter,
        diameter_stddev=diameter_stddev,
        reynolds_number=drag_evaluation.reynolds_number,
        breakup_triggered=False,
    )
    validate_droplet_state(droplet_state)
    return droplet_state


def update_droplet_state(
    *,
    previous_state: DropletState,
    gas_state: GasState,
    dx_value: float,
    drag_model: DragModel,
    distribution_model: str = "mono",
    distribution_sigma: float = 0.35,
) -> DropletState:
    """Advance the representative droplet state by one aligned axial step."""

    if dx_value <= 0.0 or not math.isfinite(dx_value):
        raise NumericalError("Droplet marching requires a positive finite axial step size.")

    slip_velocity = gas_state.velocity - previous_state.velocity
    drag_evaluation = drag_model.evaluate(
        StandardSphereDragInputs(
            gas_density=gas_state.density,
            slip_velocity=slip_velocity,
            droplet_diameter=previous_state.mean_diameter,
            dynamic_viscosity=gas_state.thermo_state.dynamic_viscosity or 1.8e-5,
        )
    )

    transport_velocity_scale = max(abs(gas_state.velocity), 1.0e-9)
    dt_value = dx_value / transport_velocity_scale
    updated_velocity = max(previous_state.velocity + drag_evaluation.acceleration * dt_value, 0.0)
    updated_slip_velocity = gas_state.velocity - updated_velocity

    smd_diameter, diameter_stddev = compute_distribution_moments(
        mean_diameter=previous_state.mean_diameter,
        maximum_diameter=previous_state.maximum_diameter,
        distribution_model=distribution_model,
        distribution_sigma=distribution_sigma,
    )

    updated_state = DropletState(
        x=gas_state.x,
        velocity=updated_velocity,
        slip_velocity=updated_slip_velocity,
        mean_diameter=previous_state.mean_diameter,
        maximum_diameter=previous_state.maximum_diameter,
        weber_number=compute_weber_number(
            gas_density=gas_state.density,
            slip_velocity=updated_slip_velocity,
            droplet_diameter=previous_state.mean_diameter,
        ),
        smd_diameter=smd_diameter,
        diameter_stddev=diameter_stddev,
        reynolds_number=drag_model.evaluate(
            StandardSphereDragInputs(
                gas_density=gas_state.density,
                slip_velocity=updated_slip_velocity,
                droplet_diameter=previous_state.mean_diameter,
                dynamic_viscosity=gas_state.thermo_state.dynamic_viscosity or 1.8e-5,
            )
        ).reynolds_number,
        breakup_triggered=False,
    )
    validate_droplet_state(updated_state)
    return updated_state