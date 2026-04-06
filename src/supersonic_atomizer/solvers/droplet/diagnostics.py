"""Droplet-solver diagnostics helpers for success and failure reporting."""

from __future__ import annotations

from typing import NoReturn
import math

from supersonic_atomizer.common import NumericalError
from supersonic_atomizer.domain import DropletState, RunDiagnostics


def create_droplet_solver_diagnostics(
    *,
    status: str,
    warnings: tuple[str, ...] = (),
    messages: tuple[str, ...] = (),
    failure_category: str | None = None,
    failure_location: str | None = None,
    last_valid_state_summary: str | None = None,
) -> RunDiagnostics:
    """Create structured diagnostics for droplet-solver runtime outputs."""

    return RunDiagnostics(
        status=status,
        warnings=warnings,
        messages=messages,
        failure_category=failure_category,
        failure_location=failure_location,
        last_valid_state_summary=last_valid_state_summary,
    )


def summarize_droplet_state(droplet_state: DropletState) -> str:
    """Return a compact last-valid-state summary for diagnostics."""

    return (
        f"x={droplet_state.x:.6f}, u_d={droplet_state.velocity:.6f}, slip={droplet_state.slip_velocity:.6f}, "
        f"d_mean={droplet_state.mean_diameter:.6e}, d_max={droplet_state.maximum_diameter:.6e}, "
        f"We={droplet_state.weber_number:.6f}"
    )


def validate_droplet_state(droplet_state: DropletState) -> None:
    """Validate local droplet-state values against runtime bounds checks."""

    if not math.isfinite(droplet_state.velocity) or droplet_state.velocity < 0.0:
        raise NumericalError("Droplet velocity checks failed: velocity must be finite and nonnegative.")
    if not math.isfinite(droplet_state.slip_velocity):
        raise NumericalError("Droplet slip checks failed: slip velocity must be finite.")
    if (
        not math.isfinite(droplet_state.mean_diameter)
        or droplet_state.mean_diameter <= 0.0
        or not math.isfinite(droplet_state.maximum_diameter)
        or droplet_state.maximum_diameter <= 0.0
    ):
        raise NumericalError("Droplet diameter checks failed: diameters must be finite and positive.")
    if droplet_state.maximum_diameter < droplet_state.mean_diameter:
        raise NumericalError(
            "Droplet state-consistency checks failed: maximum diameter must be greater than or equal to mean diameter."
        )
    if not math.isfinite(droplet_state.weber_number) or droplet_state.weber_number < 0.0:
        raise NumericalError("Droplet derived-quantity checks failed: Weber number must be finite and nonnegative.")
    if (
        droplet_state.reynolds_number is not None
        and (not math.isfinite(droplet_state.reynolds_number) or droplet_state.reynolds_number < 0.0)
    ):
        raise NumericalError(
            "Droplet derived-quantity checks failed: Reynolds number must be finite and nonnegative when present."
        )


def raise_droplet_solver_failure(
    *,
    category: str,
    message: str,
    failure_location: str | None = None,
    last_valid_state: DropletState | None = None,
) -> NoReturn:
    """Raise a droplet-side runtime failure with contextual diagnostics information."""

    parts = [category, message]
    if failure_location is not None:
        parts.append(f"location={failure_location}")
    if last_valid_state is not None:
        parts.append(f"last_valid_state={summarize_droplet_state(last_valid_state)}")
    raise NumericalError("; ".join(parts))