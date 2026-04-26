"""Runtime steam thermo provider for the supported MVP equilibrium subset."""

from __future__ import annotations

from dataclasses import dataclass

from supersonic_atomizer.common import ThermoError
from supersonic_atomizer.domain import ThermoState
from supersonic_atomizer.thermo.interfaces import ThermoProvider, ThermoProviderMetadata


def _approximate_steam_viscosity(temperature: float) -> float:
    reference_temperature = 373.15
    reference_viscosity = 1.3e-5
    return reference_viscosity * (temperature / reference_temperature) ** 0.7


@dataclass(frozen=True, slots=True)
class SteamThermoProvider(ThermoProvider):
    """Restricted equilibrium-steam provider using an idealized vapor approximation."""

    gas_constant: float = 461.5
    heat_capacity_ratio: float = 1.33
    min_pressure: float = 1_000.0
    max_pressure: float = 5_000_000.0
    min_temperature: float = 300.0
    max_temperature: float = 1_500.0

    @property
    def heat_capacity_cp(self) -> float:
        return (
            self.heat_capacity_ratio
            * self.gas_constant
            / (self.heat_capacity_ratio - 1.0)
        )

    @property
    def metadata(self) -> ThermoProviderMetadata:
        return ThermoProviderMetadata(
            provider_name="equilibrium_steam_mvp",
            working_fluid="steam",
            validity_notes=(
                "Restricted equilibrium-steam vapor subset for MVP runtime enablement.",
                "Designed as an IF97-ready placeholder behind the shared thermo interface.",
            ),
        )

    def evaluate_state(self, *, pressure: float, temperature: float) -> ThermoState:
        if pressure <= 0.0:
            raise ThermoError(
                f"Invalid steam state request: pressure must be positive, got {pressure}."
            )
        if temperature <= 0.0:
            raise ThermoError(
                f"Invalid steam state request: temperature must be positive, got {temperature}."
            )
        if pressure < self.min_pressure or pressure > self.max_pressure:
            raise ThermoError(
                "Out-of-range steam state request: "
                f"pressure {pressure} Pa is outside [{self.min_pressure}, {self.max_pressure}] Pa."
            )
        if temperature < self.min_temperature or temperature > self.max_temperature:
            raise ThermoError(
                "Out-of-range steam state request: "
                f"temperature {temperature} K is outside [{self.min_temperature}, {self.max_temperature}] K."
            )

        density = pressure / (self.gas_constant * temperature)
        enthalpy = self.heat_capacity_cp * temperature
        sound_speed = (self.heat_capacity_ratio * self.gas_constant * temperature) ** 0.5

        if density <= 0.0 or enthalpy <= 0.0 or sound_speed <= 0.0:
            raise ThermoError("Steam provider produced nonphysical thermodynamic properties.")

        return ThermoState(
            pressure=pressure,
            temperature=temperature,
            density=density,
            enthalpy=enthalpy,
            sound_speed=sound_speed,
            dynamic_viscosity=_approximate_steam_viscosity(temperature),
        )