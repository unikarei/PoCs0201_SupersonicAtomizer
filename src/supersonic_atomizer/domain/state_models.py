"""Runtime solver-state models.

These models represent local solver state and full-solution histories only.
They must remain separate from YAML parsing, plotting, and file serialization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _validate_solution_lengths(expected_length: int, lengths: dict[str, int]) -> None:
	"""Validate that all solution arrays align with the local-state history."""

	for field_name, field_length in lengths.items():
		if field_length != expected_length:
			raise ValueError(
				f"Field '{field_name}' must have length {expected_length}, got {field_length}."
			)


@dataclass(frozen=True, slots=True)
class ThermoState:
	"""Thermodynamic state at one evaluation point."""

	pressure: float
	temperature: float
	density: float
	enthalpy: float
	sound_speed: float


@dataclass(frozen=True, slots=True)
class GasState:
	"""Local gas-flow state at one axial location."""

	x: float
	area: float
	pressure: float
	temperature: float
	density: float
	velocity: float
	mach_number: float
	thermo_state: ThermoState


@dataclass(frozen=True, slots=True)
class GasSolution:
	"""Full ordered gas-solution history across the axial domain."""

	states: tuple[GasState, ...]
	x_values: tuple[float, ...]
	area_values: tuple[float, ...]
	pressure_values: tuple[float, ...]
	temperature_values: tuple[float, ...]
	density_values: tuple[float, ...]
	velocity_values: tuple[float, ...]
	mach_number_values: tuple[float, ...]
	diagnostics: Any = None

	def __post_init__(self) -> None:
		expected_length = len(self.states)
		_validate_solution_lengths(
			expected_length,
			{
				"x_values": len(self.x_values),
				"area_values": len(self.area_values),
				"pressure_values": len(self.pressure_values),
				"temperature_values": len(self.temperature_values),
				"density_values": len(self.density_values),
				"velocity_values": len(self.velocity_values),
				"mach_number_values": len(self.mach_number_values),
			},
		)


@dataclass(frozen=True, slots=True)
class DropletState:
	"""Local representative droplet state at one axial location."""

	x: float
	velocity: float
	slip_velocity: float
	mean_diameter: float
	maximum_diameter: float
	weber_number: float
	reynolds_number: float | None = None
	breakup_triggered: bool = False


@dataclass(frozen=True, slots=True)
class DropletSolution:
	"""Full ordered droplet-solution history across the axial domain."""

	states: tuple[DropletState, ...]
	x_values: tuple[float, ...]
	velocity_values: tuple[float, ...]
	slip_velocity_values: tuple[float, ...]
	mean_diameter_values: tuple[float, ...]
	maximum_diameter_values: tuple[float, ...]
	weber_number_values: tuple[float, ...]
	reynolds_number_values: tuple[float | None, ...]
	breakup_flags: tuple[bool, ...]
	diagnostics: Any = None

	def __post_init__(self) -> None:
		expected_length = len(self.states)
		_validate_solution_lengths(
			expected_length,
			{
				"x_values": len(self.x_values),
				"velocity_values": len(self.velocity_values),
				"slip_velocity_values": len(self.slip_velocity_values),
				"mean_diameter_values": len(self.mean_diameter_values),
				"maximum_diameter_values": len(self.maximum_diameter_values),
				"weber_number_values": len(self.weber_number_values),
				"reynolds_number_values": len(self.reynolds_number_values),
				"breakup_flags": len(self.breakup_flags),
			},
		)


@dataclass(frozen=True, slots=True)
class BreakupDecision:
	"""Structured local breakup-model decision."""

	triggered: bool
	weber_number: float
	critical_weber_number: float
	updated_mean_diameter: float
	updated_maximum_diameter: float
	reason: str | None = None