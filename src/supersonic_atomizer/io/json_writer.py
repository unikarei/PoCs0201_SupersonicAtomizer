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
			"x": list(simulation_result.gas_solution.x_values),
			"A": list(simulation_result.gas_solution.area_values),
			"pressure": list(simulation_result.gas_solution.pressure_values),
			"temperature": list(simulation_result.gas_solution.temperature_values),
			"density": list(simulation_result.gas_solution.density_values),
			"working_fluid_velocity": list(simulation_result.gas_solution.velocity_values),
			"Mach_number": list(simulation_result.gas_solution.mach_number_values),
			"droplet_velocity": list(simulation_result.droplet_solution.velocity_values),
			"slip_velocity": list(simulation_result.droplet_solution.slip_velocity_values),
			"droplet_mean_diameter": list(simulation_result.droplet_solution.mean_diameter_values),
			"droplet_maximum_diameter": list(simulation_result.droplet_solution.maximum_diameter_values),
			"Weber_number": list(simulation_result.droplet_solution.weber_number_values),
			"breakup_flags": list(simulation_result.droplet_solution.breakup_flags),
			"droplet_reynolds_number": list(simulation_result.droplet_solution.reynolds_number_values),
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