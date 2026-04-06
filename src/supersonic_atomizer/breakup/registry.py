"""Runtime breakup-model selection helpers."""

from __future__ import annotations

from supersonic_atomizer.common import ConfigurationError, ModelSelectionError
from supersonic_atomizer.domain import ModelSelectionConfig

from .interfaces import BreakupModel
from .weber_critical import CriticalWeberBreakupModel


def select_breakup_model(model_selection: ModelSelectionConfig) -> BreakupModel:
    """Resolve the configured runtime breakup model without silent fallbacks."""

    if model_selection.breakup_model != "weber_critical":
        raise ModelSelectionError(
            f"Unsupported breakup model '{model_selection.breakup_model}'. Supported models: weber_critical."
        )
    if model_selection.breakup_factor_mean is None or model_selection.breakup_factor_max is None:
        raise ConfigurationError(
            "The Weber-critical breakup model requires explicit breakup_factor_mean and breakup_factor_max values."
        )

    return CriticalWeberBreakupModel(
        critical_weber_number=model_selection.critical_weber_number,
        breakup_factor_mean=model_selection.breakup_factor_mean,
        breakup_factor_max=model_selection.breakup_factor_max,
    )