"""Runtime air thermo provider for the MVP foundation path."""

from __future__ import annotations

from dataclasses import dataclass

from supersonic_atomizer.common import ThermoError
from supersonic_atomizer.domain import ThermoState
from supersonic_atomizer.thermo.interfaces import ThermoProvider, ThermoProviderMetadata


@dataclass(frozen=True, slots=True)
class AirThermoProvider(ThermoProvider):
    """Simple ideal-gas air provider with constant thermophysical properties."""

    gas_constant: float = 287.05
    heat_capacity_ratio: float = 1.4
    min_pressure: float = 100.0
    max_pressure: float = 10_000_000.0
    min_temperature: float = 150.0
    max_temperature: float = 2_000.0

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
            provider_name="ideal_air",
            working_fluid="air",
            validity_notes=(
                "Ideal-gas air with constant gamma and cp.",
                "Valid for MVP air foundation cases only.",
            ),
        )

    def evaluate_state(self, *, pressure: float, temperature: float) -> ThermoState:
        if pressure <= 0.0:
            raise ThermoError(
                f"Invalid air state request: pressure must be positive, got {pressure}."
            )

        if temperature <= 0.0:
            raise ThermoError(
                f"Invalid air state request: temperature must be positive, got {temperature}."
            )

        if pressure < self.min_pressure or pressure > self.max_pressure:
            raise ThermoError(
                "Out-of-range air state request: "
                f"pressure {pressure} Pa is outside [{self.min_pressure}, {self.max_pressure}] Pa."
            )

        if temperature < self.min_temperature or temperature > self.max_temperature:
            raise ThermoError(
                "Out-of-range air state request: "
                f"temperature {temperature} K is outside [{self.min_temperature}, {self.max_temperature}] K."
            )

        density = pressure / (self.gas_constant * temperature)
        enthalpy = self.heat_capacity_cp * temperature
        sound_speed = (self.heat_capacity_ratio * self.gas_constant * temperature) ** 0.5

        if density <= 0.0 or enthalpy <= 0.0 or sound_speed <= 0.0:
            raise ThermoError("Air provider produced nonphysical thermodynamic properties.")

        return ThermoState(
            pressure=pressure,
            temperature=temperature,
            density=density,
            enthalpy=enthalpy,
            sound_speed=sound_speed,
        )