"""IF97-backed steam thermo provider for vapor-region runtime cases."""

from __future__ import annotations

from dataclasses import dataclass
import math

try:
    from iapws import IAPWS97  # optional runtime dependency
except Exception:  # pragma: no cover - optional dependency may be absent in some test envs
    IAPWS97 = None

from supersonic_atomizer.common import ThermoError
from supersonic_atomizer.domain import ThermoState
from supersonic_atomizer.thermo.interfaces import ThermoProvider, ThermoProviderMetadata


@dataclass(frozen=True, slots=True)
class IF97SteamThermoProvider(ThermoProvider):
    """Steam provider backed by the `iapws` IF97 implementation."""

    min_pressure: float = 1_000.0
    max_pressure: float = 10_000_000.0
    min_temperature: float = 273.15
    max_temperature: float = 1073.15

    @property
    def metadata(self) -> ThermoProviderMetadata:
        return ThermoProviderMetadata(
            provider_name="if97_steam_vapor",
            working_fluid="steam",
            validity_notes=(
                "IF97-backed steam provider using the iapws package.",
                "Current runtime support is limited to direct P-T vapor-region evaluations.",
            ),
        )

    @property
    def heat_capacity_ratio(self) -> float:
        return 1.33

    def evaluate_state(self, *, pressure: float, temperature: float) -> ThermoState:
        if pressure <= 0.0 or not math.isfinite(pressure):
            raise ThermoError(f"Invalid IF97 steam state request: pressure must be positive, got {pressure}.")
        if temperature <= 0.0 or not math.isfinite(temperature):
            raise ThermoError(
                f"Invalid IF97 steam state request: temperature must be positive, got {temperature}."
            )
        if pressure < self.min_pressure or pressure > self.max_pressure:
            raise ThermoError(
                "Out-of-range IF97 steam state request: "
                f"pressure {pressure} Pa is outside [{self.min_pressure}, {self.max_pressure}] Pa."
            )
        if temperature < self.min_temperature or temperature > self.max_temperature:
            raise ThermoError(
                "Out-of-range IF97 steam state request: "
                f"temperature {temperature} K is outside [{self.min_temperature}, {self.max_temperature}] K."
            )

        try:
            if IAPWS97 is None:
                raise RuntimeError("iapws library is not installed; IF97 provider unavailable.")
            state = IAPWS97(P=pressure / 1_000_000.0, T=temperature)
        except Exception as exc:  # pragma: no cover
            raise ThermoError(f"IF97 steam provider failed to evaluate state: {exc}") from exc

        if getattr(state, "region", None) not in {2, 5}:
            raise ThermoError(
                "IF97 steam provider currently supports vapor-region P-T states only; "
                f"received region {getattr(state, 'region', 'unknown')}."
            )

        density = float(state.rho)
        enthalpy = float(state.h) * 1_000.0
        sound_speed = float(state.w)
        dynamic_viscosity = float(state.mu)
        if (
            density <= 0.0
            or enthalpy <= 0.0
            or sound_speed <= 0.0
            or dynamic_viscosity <= 0.0
            or not math.isfinite(density)
            or not math.isfinite(enthalpy)
            or not math.isfinite(sound_speed)
            or not math.isfinite(dynamic_viscosity)
        ):
            raise ThermoError("IF97 steam provider produced nonphysical thermodynamic properties.")

        return ThermoState(
            pressure=pressure,
            temperature=temperature,
            density=density,
            enthalpy=enthalpy,
            sound_speed=sound_speed,
            dynamic_viscosity=dynamic_viscosity,
        )