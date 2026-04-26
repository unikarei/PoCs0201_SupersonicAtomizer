"""Runtime validation reporting helpers."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable

from supersonic_atomizer.domain import SimulationResult, ValidationReport


@dataclass(frozen=True, slots=True)
class ValidationCheckResult:
    """Structured result for one runtime validation check."""

    name: str
    status: str
    observation: str


@dataclass(frozen=True, slots=True)
class ValidationMetricTarget:
    """Reference target for one quantitative validation metric."""

    metric_name: str
    target_value: float
    tolerance: float
    weight: float = 1.0


@dataclass(frozen=True, slots=True)
class CaseObjectiveResult:
    """Objective summary for one validation case."""

    case_name: str
    weighted_rmse: float
    metric_errors: dict[str, float]
    metric_within_tolerance: dict[str, bool]


@dataclass(frozen=True, slots=True)
class ValidationCampaignReport:
    """Structured quantitative validation report for a case campaign."""

    status: str
    case_results: tuple[CaseObjectiveResult, ...]
    baseline_objective: float
    observations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SensitivityResult:
    """One-at-a-time normalized sensitivity output for one parameter."""

    parameter_name: str
    baseline_objective: float
    perturbed_objective: float
    normalized_sensitivity: float


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    """Bounded candidate optimization result."""

    best_parameters: dict[str, float]
    best_objective: float
    evaluations: int


@dataclass(frozen=True, slots=True)
class ObjectiveUncertaintySummary:
    """Uncertainty summary for sampled objective values."""

    sample_count: int
    objective_mean: float
    objective_stddev: float
    ci95_lower: float
    ci95_upper: float


def assemble_validation_report(check_results: tuple[ValidationCheckResult, ...]) -> ValidationReport:
    """Assemble a structured validation report from individual check outcomes."""

    checks_run = len(check_results)
    checks_passed = sum(1 for result in check_results if result.status == "pass")
    checks_warned = sum(1 for result in check_results if result.status == "warn")
    checks_failed = sum(1 for result in check_results if result.status == "fail")
    if checks_failed > 0:
        status = "fail"
    elif checks_warned > 0:
        status = "warn"
    else:
        status = "pass"
    return ValidationReport(
        status=status,
        checks_run=checks_run,
        checks_passed=checks_passed,
        checks_warned=checks_warned,
        checks_failed=checks_failed,
        observations=tuple(result.observation for result in check_results),
    )


def documented_validation_case_registry() -> dict[str, str]:
    """Return documented validation-case mapping used by quantitative workflows."""

    return {
        "constant_area_gas_only": "docs/gas-only-validation-cases.md",
        "converging_diverging_sanity": "docs/gas-only-validation-cases.md",
        "zero_or_near_zero_slip": "docs/droplet-transport-validation-cases.md",
        "slip_driven_acceleration": "docs/droplet-transport-validation-cases.md",
        "breakup_trigger_case": "docs/breakup-validation-cases.md",
    }


def evaluate_validation_campaign(
    *,
    observed_case_metrics: dict[str, dict[str, float]],
    reference_targets: dict[str, tuple[ValidationMetricTarget, ...]],
) -> ValidationCampaignReport:
    """Evaluate weighted objective errors for documented validation cases."""

    case_results: list[CaseObjectiveResult] = []
    observations: list[str] = []
    failures = 0

    for case_name, targets in reference_targets.items():
        observed_metrics = observed_case_metrics.get(case_name)
        if observed_metrics is None:
            failures += 1
            observations.append(f"missing_case_metrics={case_name}")
            continue

        weighted_error_sum = 0.0
        weight_sum = 0.0
        metric_errors: dict[str, float] = {}
        metric_within_tolerance: dict[str, bool] = {}

        for target in targets:
            if target.tolerance <= 0.0:
                raise ValueError(f"Target tolerance must be positive for metric '{target.metric_name}'.")
            if target.weight <= 0.0:
                raise ValueError(f"Target weight must be positive for metric '{target.metric_name}'.")

            observed_value = observed_metrics.get(target.metric_name)
            if observed_value is None:
                failures += 1
                observations.append(f"missing_metric={case_name}:{target.metric_name}")
                continue

            metric_error = observed_value - target.target_value
            metric_errors[target.metric_name] = metric_error
            within_tolerance = abs(metric_error) <= target.tolerance
            metric_within_tolerance[target.metric_name] = within_tolerance
            if not within_tolerance:
                failures += 1

            weighted_error_sum += target.weight * metric_error * metric_error
            weight_sum += target.weight

        if weight_sum <= 0.0:
            failures += 1
            observations.append(f"invalid_weight_sum={case_name}")
            continue

        case_rmse = math.sqrt(weighted_error_sum / weight_sum)
        case_results.append(
            CaseObjectiveResult(
                case_name=case_name,
                weighted_rmse=case_rmse,
                metric_errors=metric_errors,
                metric_within_tolerance=metric_within_tolerance,
            )
        )
        observations.append(f"case_objective={case_name}:{case_rmse:.6e}")

    if not case_results:
        raise ValueError("Validation campaign produced no evaluable case results.")

    baseline_objective = sum(case.weighted_rmse for case in case_results) / len(case_results)
    status = "pass" if failures == 0 else "warn"
    observations.append(f"baseline_objective={baseline_objective:.6e}")

    return ValidationCampaignReport(
        status=status,
        case_results=tuple(case_results),
        baseline_objective=baseline_objective,
        observations=tuple(observations),
    )


def run_one_at_a_time_sensitivity(
    *,
    baseline_parameters: dict[str, float],
    perturbation_factors: dict[str, float],
    objective_function: Callable[[dict[str, float]], float],
) -> tuple[SensitivityResult, ...]:
    """Compute normalized one-at-a-time sensitivity coefficients."""

    baseline_objective = objective_function(dict(baseline_parameters))
    if not math.isfinite(baseline_objective):
        raise ValueError("Baseline objective must be finite.")

    results: list[SensitivityResult] = []
    for parameter_name, baseline_value in baseline_parameters.items():
        factor = perturbation_factors.get(parameter_name, 1.05)
        if factor <= 0.0 or math.isclose(factor, 1.0, rel_tol=0.0, abs_tol=1.0e-12):
            raise ValueError(f"Perturbation factor must be positive and not equal to 1.0 for '{parameter_name}'.")

        perturbed_parameters = dict(baseline_parameters)
        perturbed_parameters[parameter_name] = baseline_value * factor
        perturbed_objective = objective_function(perturbed_parameters)
        if not math.isfinite(perturbed_objective):
            raise ValueError(f"Perturbed objective must be finite for parameter '{parameter_name}'.")

        parameter_delta = perturbed_parameters[parameter_name] - baseline_value
        if math.isclose(parameter_delta, 0.0, rel_tol=0.0, abs_tol=1.0e-15):
            normalized_sensitivity = 0.0
        else:
            normalized_sensitivity = (
                (perturbed_objective - baseline_objective) / parameter_delta
            ) * (baseline_value / max(abs(baseline_objective), 1.0e-12))

        results.append(
            SensitivityResult(
                parameter_name=parameter_name,
                baseline_objective=baseline_objective,
                perturbed_objective=perturbed_objective,
                normalized_sensitivity=normalized_sensitivity,
            )
        )

    results.sort(key=lambda entry: abs(entry.normalized_sensitivity), reverse=True)
    return tuple(results)


def run_candidate_optimization(
    *,
    candidates: tuple[dict[str, float], ...],
    objective_function: Callable[[dict[str, float]], float],
) -> OptimizationResult:
    """Run bounded candidate optimization and return the best objective."""

    if not candidates:
        raise ValueError("At least one candidate parameter set is required for optimization.")

    best_parameters = dict(candidates[0])
    best_objective = objective_function(best_parameters)
    if not math.isfinite(best_objective):
        raise ValueError("Objective function returned non-finite value for first candidate.")

    for candidate in candidates[1:]:
        objective_value = objective_function(dict(candidate))
        if not math.isfinite(objective_value):
            raise ValueError("Objective function returned non-finite value during optimization.")
        if objective_value < best_objective:
            best_objective = objective_value
            best_parameters = dict(candidate)

    return OptimizationResult(
        best_parameters=best_parameters,
        best_objective=best_objective,
        evaluations=len(candidates),
    )


def summarize_objective_uncertainty(samples: tuple[float, ...]) -> ObjectiveUncertaintySummary:
    """Summarize objective uncertainty using mean/stddev and normal 95% CI."""

    if not samples:
        raise ValueError("At least one objective sample is required.")
    if not all(math.isfinite(value) for value in samples):
        raise ValueError("Objective samples must be finite.")

    sample_count = len(samples)
    objective_mean = sum(samples) / sample_count
    if sample_count == 1:
        objective_stddev = 0.0
        ci_half_width = 0.0
    else:
        variance = sum((value - objective_mean) ** 2 for value in samples) / (sample_count - 1)
        objective_stddev = math.sqrt(max(variance, 0.0))
        ci_half_width = 1.96 * objective_stddev / math.sqrt(sample_count)

    return ObjectiveUncertaintySummary(
        sample_count=sample_count,
        objective_mean=objective_mean,
        objective_stddev=objective_stddev,
        ci95_lower=objective_mean - ci_half_width,
        ci95_upper=objective_mean + ci_half_width,
    )


def validate_simulation_result(simulation_result: SimulationResult) -> ValidationReport:
    """Execute runtime sanity checks and assemble the final validation report."""

    from .sanity_checks import run_sanity_checks

    return assemble_validation_report(run_sanity_checks(simulation_result))