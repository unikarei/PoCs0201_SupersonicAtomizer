"""Runtime thermo-provider contract definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from supersonic_atomizer.domain import ThermoState


@dataclass(frozen=True, slots=True)
class ThermoProviderMetadata:
    """Metadata exposed by a thermo provider for selection and diagnostics."""

    provider_name: str
    working_fluid: str
    validity_notes: tuple[str, ...] = ()


class ThermoProvider(ABC):
    """Abstract thermo-provider interface used by gas-side runtime code."""

    @property
    @abstractmethod
    def metadata(self) -> ThermoProviderMetadata:
        """Return provider metadata and validity notes."""

    @abstractmethod
    def evaluate_state(self, *, pressure: float, temperature: float) -> ThermoState:
        """Evaluate a thermodynamic state from SI pressure and temperature."""

    @property
    def provider_name(self) -> str:
        return self.metadata.provider_name

    @property
    def working_fluid(self) -> str:
        return self.metadata.working_fluid

    @property
    def validity_notes(self) -> tuple[str, ...]:
        return self.metadata.validity_notes