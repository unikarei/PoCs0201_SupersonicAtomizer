"""Runtime validation reporting helpers."""

from __future__ import annotations

from dataclasses import dataclass

from supersonic_atomizer.domain import SimulationResult, ValidationReport


@dataclass(frozen=True, slots=True)
class ValidationCheckResult:
    """Structured result for one runtime validation check."""

    name: str
    status: str
    observation: str


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


def validate_simulation_result(simulation_result: SimulationResult) -> ValidationReport:
    """Execute runtime sanity checks and assemble the final validation report."""

    from .sanity_checks import run_sanity_checks

    return assemble_validation_report(run_sanity_checks(simulation_result))