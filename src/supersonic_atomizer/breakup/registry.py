"""Runtime breakup-model selection helpers."""

from __future__ import annotations

from supersonic_atomizer.common import ConfigurationError, ModelSelectionError
from supersonic_atomizer.domain import ModelSelectionConfig

from .bag_stripping import BagStrippingBreakupModel
from .interfaces import BreakupModel
from .khrt import KHRTBreakupModel
from .weber_critical import CriticalWeberBreakupModel


def select_breakup_model(model_selection: ModelSelectionConfig) -> BreakupModel:
    """Resolve the configured runtime breakup model without silent fallbacks."""

    breakup_model_name = model_selection.breakup_model

    if breakup_model_name == "weber_critical":
        if model_selection.breakup_factor_mean is None or model_selection.breakup_factor_max is None:
            raise ConfigurationError(
                "The Weber-critical breakup model requires explicit breakup_factor_mean and breakup_factor_max values."
            )
        return CriticalWeberBreakupModel(
            critical_weber_number=model_selection.critical_weber_number,
            breakup_factor_mean=model_selection.breakup_factor_mean,
            breakup_factor_max=model_selection.breakup_factor_max,
        )

    if breakup_model_name == "khrt":
        return KHRTBreakupModel(
            B0=model_selection.khrt_B0,
            B1=model_selection.khrt_B1,
            Crt=model_selection.khrt_Crt,
            liquid_density=model_selection.liquid_density,
            liquid_viscosity=model_selection.liquid_viscosity,
        )

    if breakup_model_name == "bag_stripping":
        return BagStrippingBreakupModel(
            critical_weber_number=model_selection.critical_weber_number,
        )

    raise ModelSelectionError(
        f"Unsupported breakup model '{breakup_model_name}'. "
        "Supported models: weber_critical, khrt, bag_stripping."
    )
