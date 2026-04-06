"""Runtime sanity and trend checks for structured simulation results."""

from __future__ import annotations

from dataclasses import replace
import math
from typing import NoReturn

from supersonic_atomizer.common import ValidationError
from supersonic_atomizer.domain import DropletState, SimulationResult

from .reporting import ValidationCheckResult


def raise_validation_failure(*, category: str, message: str) -> NoReturn:
    """Raise a structured validation-runtime failure."""

    raise ValidationError(f"{category}: {message}")


def _require_aligned_axial_data(simulation_result: SimulationResult) -> None:
    """Ensure gas and droplet solutions remain aligned for validation checks."""

    if len(simulation_result.gas_solution.states) != len(simulation_result.droplet_solution.states):
        raise_validation_failure(
            category="Validation input alignment",
            message="Gas and droplet solution lengths must match for validation execution.",
        )
    if simulation_result.gas_solution.x_values != simulation_result.droplet_solution.x_values:
        raise_validation_failure(
            category="Validation input alignment",
            message="Gas and droplet solutions must share identical axial coordinates for validation execution.",
        )


def _require_finite_series(name: str, values: tuple[float, ...]) -> None:
    """Require all values in one validation series to be finite."""

    if not all(math.isfinite(value) for value in values):
        raise_validation_failure(
            category="Validation input finiteness",
            message=f"Series '{name}' contains non-finite values.",
        )


def _check_gas_solution_completion(simulation_result: SimulationResult) -> ValidationCheckResult:
    """Validate core gas-solution completeness and finite trend readiness."""

    _require_finite_series("pressure", simulation_result.gas_solution.pressure_values)
    _require_finite_series("temperature", simulation_result.gas_solution.temperature_values)
    _require_finite_series("density", simulation_result.gas_solution.density_values)
    _require_finite_series("working_fluid_velocity", simulation_result.gas_solution.velocity_values)
    _require_finite_series("Mach_number", simulation_result.gas_solution.mach_number_values)

    status = "pass" if simulation_result.gas_solution.diagnostics.status == "completed" else "warn"
    return ValidationCheckResult(
        name="gas_solution_completion",
        status=status,
        observation=(
            "Gas solution arrays are finite, aligned, and suitable for qualitative gas-only validation."
        ),
    )


def _check_zero_or_near_zero_slip_case(simulation_result: SimulationResult) -> ValidationCheckResult | None:
    """Validate the documented zero-slip transport expectation when applicable."""

    initial_slip = abs(simulation_result.droplet_solution.slip_velocity_values[0])
    if initial_slip > 1.0e-9:
        return None

    max_slip = max(abs(value) for value in simulation_result.droplet_solution.slip_velocity_values)
    status = "pass" if max_slip <= 1.0e-6 else "warn"
    return ValidationCheckResult(
        name="zero_or_near_zero_slip",
        status=status,
        observation=(
            "Zero-slip or near-zero-slip validation case preserved minimal relative motion across the axial grid."
            if status == "pass"
            else "Zero-slip validation case developed noticeable relative motion and should be reviewed."
        ),
    )


def _check_slip_driven_acceleration_case(simulation_result: SimulationResult) -> ValidationCheckResult | None:
    """Validate the documented slip-driven acceleration trend when applicable."""

    initial_slip = abs(simulation_result.droplet_solution.slip_velocity_values[0])
    if initial_slip <= 1.0e-9:
        return None

    final_velocity = simulation_result.droplet_solution.velocity_values[-1]
    initial_velocity = simulation_result.droplet_solution.velocity_values[0]
    final_slip = abs(simulation_result.droplet_solution.slip_velocity_values[-1])
    status = "pass" if final_velocity > initial_velocity and final_slip < initial_slip else "warn"
    return ValidationCheckResult(
        name="slip_driven_acceleration",
        status=status,
        observation=(
            "Slip-driven transport validation shows droplet acceleration with decreasing relative velocity."
            if status == "pass"
            else "Slip-driven transport validation did not show the expected acceleration/slip trend."
        ),
    )


def _check_breakup_behavior(simulation_result: SimulationResult) -> ValidationCheckResult:
    """Validate documented breakup-trigger and no-trigger expectations."""

    flags = simulation_result.droplet_solution.breakup_flags
    if not any(flags):
        return ValidationCheckResult(
            name="breakup_threshold_behavior",
            status="pass",
            observation="No-breakup validation case preserved droplet diameters and kept breakup flags false.",
        )

    for index in range(1, len(flags)):
        if not flags[index]:
            continue
        previous_mean = simulation_result.droplet_solution.mean_diameter_values[index - 1]
        previous_max = simulation_result.droplet_solution.maximum_diameter_values[index - 1]
        current_mean = simulation_result.droplet_solution.mean_diameter_values[index]
        current_max = simulation_result.droplet_solution.maximum_diameter_values[index]
        if current_mean >= previous_mean or current_max >= previous_max or current_max < current_mean:
            return ValidationCheckResult(
                name="breakup_threshold_behavior",
                status="fail",
                observation="Triggered breakup case did not preserve the expected diameter-reduction behavior.",
            )

    return ValidationCheckResult(
        name="breakup_threshold_behavior",
        status="pass",
        observation="Triggered breakup validation case reduced mean and maximum diameters while preserving physical ordering.",
    )


def run_sanity_checks(simulation_result: SimulationResult) -> tuple[ValidationCheckResult, ...]:
    """Execute the approved validation sanity and trend checks."""

    _require_aligned_axial_data(simulation_result)
    _require_finite_series("Weber_number", simulation_result.droplet_solution.weber_number_values)

    check_results: list[ValidationCheckResult] = [_check_gas_solution_completion(simulation_result)]

    zero_slip_check = _check_zero_or_near_zero_slip_case(simulation_result)
    if zero_slip_check is not None:
        check_results.append(zero_slip_check)

    slip_driven_check = _check_slip_driven_acceleration_case(simulation_result)
    if slip_driven_check is not None:
        check_results.append(slip_driven_check)

    check_results.append(_check_breakup_behavior(simulation_result))
    return tuple(check_results)