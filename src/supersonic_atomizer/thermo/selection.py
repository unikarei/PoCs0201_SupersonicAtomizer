"""Runtime thermo backend selection for supported foundation cases."""

from __future__ import annotations

from supersonic_atomizer.common import ModelSelectionError
from supersonic_atomizer.domain import CaseConfig
from supersonic_atomizer.thermo.air import AirThermoProvider
from supersonic_atomizer.thermo.interfaces import ThermoProvider


def select_thermo_provider(case_config: CaseConfig) -> ThermoProvider:
    """Select the configured thermo provider for the current foundation path."""

    working_fluid = case_config.fluid.working_fluid
    steam_property_model = case_config.models.steam_property_model

    if working_fluid == "air":
        return AirThermoProvider()

    if working_fluid == "steam":
        if steam_property_model is not None:
            raise ModelSelectionError(
                "Unsupported steam thermo backend selection: "
                f"'{steam_property_model}' is not available in the current foundation path."
            )

        raise ModelSelectionError(
            "Steam thermo selection is not yet available in the current foundation path."
        )

    raise ModelSelectionError(
        f"Unsupported working fluid for thermo selection: '{working_fluid}'."
    )