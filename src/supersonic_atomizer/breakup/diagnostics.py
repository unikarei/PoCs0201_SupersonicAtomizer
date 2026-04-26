"""Breakup-runtime diagnostics helpers."""

from __future__ import annotations

import math

from supersonic_atomizer.common import NumericalError
from supersonic_atomizer.domain import BreakupDecision


def validate_breakup_decision(decision: BreakupDecision) -> None:
    """Validate a local breakup decision against MVP runtime expectations."""

    if not math.isfinite(decision.weber_number) or decision.weber_number < 0.0:
        raise NumericalError("Breakup decision checks failed: Weber number must be finite and nonnegative.")
    if not math.isfinite(decision.critical_weber_number) or decision.critical_weber_number < 0.0:
        raise NumericalError(
            "Breakup decision checks failed: critical Weber number must be finite and nonnegative "
            "(use 0.0 for physics-based models that have no scalar threshold)."
        )
    if (
        not math.isfinite(decision.updated_mean_diameter)
        or decision.updated_mean_diameter <= 0.0
        or not math.isfinite(decision.updated_maximum_diameter)
        or decision.updated_maximum_diameter <= 0.0
    ):
        raise NumericalError(
            "Breakup decision checks failed: updated diameters must be finite and positive."
        )
    if decision.updated_maximum_diameter < decision.updated_mean_diameter:
        raise NumericalError(
            "Breakup decision checks failed: updated maximum diameter must be greater than or equal to updated mean diameter."
        )