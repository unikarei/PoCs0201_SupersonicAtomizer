"""Gas-solver diagnostics helpers for success and failure reporting."""

from __future__ import annotations

from typing import NoReturn

from supersonic_atomizer.common import NumericalError
from supersonic_atomizer.domain import GasState, RunDiagnostics


def create_gas_solver_diagnostics(
    *,
    status: str,
    warnings: tuple[str, ...] = (),
    messages: tuple[str, ...] = (),
    failure_category: str | None = None,
    failure_location: str | None = None,
    last_valid_state_summary: str | None = None,
) -> RunDiagnostics:
    """Create structured diagnostics for gas-solver runtime outputs."""

    return RunDiagnostics(
        status=status,
        warnings=warnings,
        messages=messages,
        failure_category=failure_category,
        failure_location=failure_location,
        last_valid_state_summary=last_valid_state_summary,
    )


def summarize_gas_state(gas_state: GasState) -> str:
    """Return a compact last-valid-state summary for diagnostics."""

    return (
        f"x={gas_state.x:.6f}, p={gas_state.pressure:.6f}, T={gas_state.temperature:.6f}, "
        f"rho={gas_state.density:.6f}, u={gas_state.velocity:.6f}, M={gas_state.mach_number:.6f}"
    )


def raise_gas_solver_failure(
    *,
    category: str,
    message: str,
    failure_location: str | None = None,
    last_valid_state: GasState | None = None,
) -> NoReturn:
    """Raise a gas-side runtime failure with contextual diagnostics information."""

    parts = [category, message]
    if failure_location is not None:
        parts.append(f"location={failure_location}")
    if last_valid_state is not None:
        parts.append(f"last_valid_state={summarize_gas_state(last_valid_state)}")

    raise NumericalError("; ".join(parts))