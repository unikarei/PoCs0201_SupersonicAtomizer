"""Runtime Matplotlib profile plotting for structured simulation results."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from matplotlib import pyplot as plt

from supersonic_atomizer.common import OutputError
from supersonic_atomizer.domain import OutputMetadata, SimulationResult

from .styles import PLOT_LABELS


def _plot_series(*, x_values: tuple[float, ...], y_values: tuple[float, ...], title: str, y_label: str, path: str) -> None:
	"""Write one line profile plot to the target path."""

	figure, axis = plt.subplots(figsize=(6.0, 4.0))
	axis.plot(x_values, y_values, linewidth=2.0)
	axis.set_xlabel("x [m]")
	axis.set_ylabel(y_label)
	axis.set_title(title)
	axis.grid(True)
	figure.tight_layout()
	figure.savefig(path)
	plt.close(figure)


def _resolve_output_metadata(simulation_result: SimulationResult, output_metadata: OutputMetadata | None) -> OutputMetadata:
	"""Resolve the plotting artifact metadata from explicit input or the result object."""

	resolved_metadata = output_metadata or simulation_result.output_metadata
	if resolved_metadata is None:
		raise OutputError("Profile plotting requires explicit output metadata or simulation-result output metadata.")
	if not resolved_metadata.plot_paths:
		raise OutputError("Profile plotting requires configured plot artifact paths.")
	return resolved_metadata


def generate_profile_plots(
	simulation_result: SimulationResult,
	output_metadata: OutputMetadata | None = None,
) -> dict[str, str]:
	"""Generate the required MVP profile plots from structured result data only."""

	resolved_metadata = _resolve_output_metadata(simulation_result, output_metadata)
	series_map: dict[str, tuple[float, ...]] = {
		"pressure": simulation_result.gas_solution.pressure_values,
		"temperature": simulation_result.gas_solution.temperature_values,
		"working_fluid_velocity": simulation_result.gas_solution.velocity_values,
		"droplet_velocity": simulation_result.droplet_solution.velocity_values,
		"mach_number": simulation_result.gas_solution.mach_number_values,
		"droplet_mean_diameter": simulation_result.droplet_solution.mean_diameter_values,
		"droplet_maximum_diameter": simulation_result.droplet_solution.maximum_diameter_values,
		"weber_number": simulation_result.droplet_solution.weber_number_values,
	}

	try:
		for plot_name, y_values in series_map.items():
			plot_path = resolved_metadata.plot_paths.get(plot_name)
			if plot_path is None:
				raise OutputError(f"Profile plotting is missing a configured path for '{plot_name}'.")
			Path(plot_path).parent.mkdir(parents=True, exist_ok=True)
			title, y_label = PLOT_LABELS[plot_name]
			_plot_series(
				x_values=simulation_result.gas_solution.x_values,
				y_values=y_values,
				title=title,
				y_label=y_label,
				path=plot_path,
			)
	except OSError as exc:
		raise OutputError(f"Plot-generation failure for '{resolved_metadata.output_directory}': {exc}") from exc

	return resolved_metadata.plot_paths