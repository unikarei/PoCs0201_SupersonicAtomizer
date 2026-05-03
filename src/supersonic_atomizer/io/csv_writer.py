"""Runtime CSV serialization for structured simulation results.

CSV files now include a leading comment line with a JSON map of column units
to make downstream tooling and users aware of the stored SI units.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from supersonic_atomizer.common import OutputError
from supersonic_atomizer.domain import SimulationResult


CSV_COLUMNS: tuple[str, ...] = (
	"x",
	"A",
	"pressure",
	"temperature",
	"density",
	"working_fluid_velocity",
	"Mach_number",
	"droplet_velocity",
	"slip_velocity",
	"droplet_mean_diameter",
	"droplet_maximum_diameter",
	"Weber_number",
	"breakup_flag",
	"droplet_reynolds_number",
)


def _resolve_csv_path(simulation_result: SimulationResult, csv_path: str | None) -> Path:
	"""Resolve the CSV destination path from explicit input or output metadata."""

	resolved_path = csv_path
	if resolved_path is None and simulation_result.output_metadata is not None:
		resolved_path = simulation_result.output_metadata.csv_path
	if resolved_path is None:
		raise OutputError("CSV serialization requires an explicit destination path or output metadata csv_path.")
	return Path(resolved_path)


def write_simulation_result_csv(simulation_result: SimulationResult, csv_path: str | None = None) -> str:
	"""Write aligned simulation-result axial data to CSV."""

	resolved_path = _resolve_csv_path(simulation_result, csv_path)
	try:
		resolved_path.parent.mkdir(parents=True, exist_ok=True)
		with resolved_path.open("w", encoding="utf-8", newline="") as handle:
			# Write a single-unit metadata comment as the first line. This is a
			# human-friendly hint and machine-parsable JSON when the consumer
			# understands the '# UNITS:' prefix.
			units_map = {
				"x": "m",
				"A": "m^2",
				"pressure": "Pa",
				"temperature": "K",
				"density": "kg/m^3",
				"working_fluid_velocity": "m/s",
				"Mach_number": "-",
				"droplet_velocity": "m/s",
				"slip_velocity": "m/s",
				"droplet_mean_diameter": "m",
				"droplet_maximum_diameter": "m",
				"Weber_number": "-",
				"breakup_flag": "bool",
				"droplet_reynolds_number": "-",
			}
			handle.write(f"# UNITS: {json.dumps(units_map)}\n")
			writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
			writer.writeheader()
			for index, x_value in enumerate(simulation_result.gas_solution.x_values):
				writer.writerow(
					{
						"x": x_value,
						"A": simulation_result.gas_solution.area_values[index],
						"pressure": simulation_result.gas_solution.pressure_values[index],
						"temperature": simulation_result.gas_solution.temperature_values[index],
						"density": simulation_result.gas_solution.density_values[index],
						"working_fluid_velocity": simulation_result.gas_solution.velocity_values[index],
						"Mach_number": simulation_result.gas_solution.mach_number_values[index],
						"droplet_velocity": simulation_result.droplet_solution.velocity_values[index],
						"slip_velocity": simulation_result.droplet_solution.slip_velocity_values[index],
						"droplet_mean_diameter": simulation_result.droplet_solution.mean_diameter_values[index],
						"droplet_maximum_diameter": simulation_result.droplet_solution.maximum_diameter_values[index],
						"Weber_number": simulation_result.droplet_solution.weber_number_values[index],
						"breakup_flag": simulation_result.droplet_solution.breakup_flags[index],
						"droplet_reynolds_number": simulation_result.droplet_solution.reynolds_number_values[index],
					}
				)
	except OSError as exc:
		raise OutputError(f"CSV write failure for '{resolved_path}': {exc}") from exc

	return str(resolved_path)