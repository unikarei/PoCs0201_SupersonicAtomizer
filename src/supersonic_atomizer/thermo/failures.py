"""Thermo evaluation helpers that preserve repository error categories."""

from __future__ import annotations

from supersonic_atomizer.common import ThermoError
from supersonic_atomizer.domain import ThermoState
from supersonic_atomizer.thermo.interfaces import ThermoProvider


def evaluate_thermo_state(
    provider: ThermoProvider,
    *,
    pressure: float,
    temperature: float,
) -> ThermoState:
    """Evaluate thermo state while preserving thermo-specific failure categorization."""

    try:
        return provider.evaluate_state(pressure=pressure, temperature=temperature)
    except ThermoError:
        raise
    except Exception as exc:
        raise ThermoError(
            "Thermo evaluation failed for provider "
            f"'{provider.provider_name}' with pressure={pressure} Pa and temperature={temperature} K."
        ) from exc