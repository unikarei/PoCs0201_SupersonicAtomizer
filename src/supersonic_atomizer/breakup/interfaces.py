"""Runtime breakup-model interfaces and structured inputs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from supersonic_atomizer.domain import BreakupDecision, DropletState, GasState


@dataclass(frozen=True, slots=True)
class BreakupModelInputs:
    """Structured local inputs consumed by runtime breakup models."""

    gas_state: GasState
    droplet_state: DropletState
    dt: float | None = None  # estimated local interaction time (s), may be None


class BreakupModel(ABC):
    """Abstract runtime breakup-model contract."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the stable configuration-facing model name."""

    @abstractmethod
    def evaluate(self, inputs: BreakupModelInputs) -> BreakupDecision:
        """Return a structured local breakup decision."""