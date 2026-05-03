"""Runtime JSON serialization for structured simulation results."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from supersonic_atomizer.common import OutputError
from supersonic_atomizer.domain import SimulationResult


def simulation_result_to_dict(simulation_result: SimulationResult) -> dict[str, object]:
	"""Convert a structured simulation result into the approved JSON-ready shape."""

	metadata: dict[str, object] = {
		"case_name": simulation_result.case_name,
		"working_fluid": simulation_result.working_fluid,
	}
	if simulation_result.output_metadata is not None:
		metadata["output_metadata"] = asdict(simulation_result.output_metadata)

	payload: dict[str, object] = {
		"metadata": metadata,
		"settings_summary": simulation_result.settings_summary,
		"numerical_results": {
			"x": {"values": list(simulation_result.gas_solution.x_values), "unit": "m"},
			"A": {"values": list(simulation_result.gas_solution.area_values), "unit": "m^2"},
			"pressure": {"values": list(simulation_result.gas_solution.pressure_values), "unit": "Pa"},
			"temperature": {"values": list(simulation_result.gas_solution.temperature_values), "unit": "K"},
			"density": {"values": list(simulation_result.gas_solution.density_values), "unit": "kg/m^3"},
			"working_fluid_velocity": {"values": list(simulation_result.gas_solution.velocity_values), "unit": "m/s"},
			"Mach_number": {"values": list(simulation_result.gas_solution.mach_number_values), "unit": "-"},
			"droplet_velocity": {"values": list(simulation_result.droplet_solution.velocity_values), "unit": "m/s"},
			"slip_velocity": {"values": list(simulation_result.droplet_solution.slip_velocity_values), "unit": "m/s"},
			"droplet_mean_diameter": {"values": list(simulation_result.droplet_solution.mean_diameter_values), "unit": "m"},
			"droplet_maximum_diameter": {"values": list(simulation_result.droplet_solution.maximum_diameter_values), "unit": "m"},
			"Weber_number": {"values": list(simulation_result.droplet_solution.weber_number_values), "unit": "-"},
			"breakup_flags": {"values": list(simulation_result.droplet_solution.breakup_flags), "unit": "bool"},
			"droplet_reynolds_number": {"values": list(simulation_result.droplet_solution.reynolds_number_values), "unit": "-"},
		},
		"units": {
			"internal": "SI",
			"preferred_display": {
				"temperature": "K",
				"pressure": "kPa",
				"length": "m",
				"velocity": "m/s"
			}
		},
		"diagnostics": asdict(simulation_result.diagnostics),
	}
	if simulation_result.validation_report is not None:
		payload["validation_report"] = asdict(simulation_result.validation_report)
	return payload


def _resolve_json_path(simulation_result: SimulationResult, json_path: str | None) -> Path:
	"""Resolve the JSON destination path from explicit input or output metadata."""

	resolved_path = json_path
	if resolved_path is None and simulation_result.output_metadata is not None:
		resolved_path = simulation_result.output_metadata.json_path
	if resolved_path is None:
		raise OutputError("JSON serialization requires an explicit destination path or output metadata json_path.")
	return Path(resolved_path)


def write_simulation_result_json(simulation_result: SimulationResult, json_path: str | None = None) -> str:
	"""Write the structured simulation result as JSON."""

	resolved_path = _resolve_json_path(simulation_result, json_path)
	try:
		resolved_path.parent.mkdir(parents=True, exist_ok=True)
		with resolved_path.open("w", encoding="utf-8") as handle:
			json.dump(simulation_result_to_dict(simulation_result), handle, indent=2)
	except OSError as exc:
		raise OutputError(f"JSON write failure for '{resolved_path}': {exc}") from exc

	return str(resolved_path)