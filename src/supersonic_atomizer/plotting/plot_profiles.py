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
		"area_profile": simulation_result.gas_solution.area_values,
		"slip_velocity": simulation_result.droplet_solution.slip_velocity_values,
	}

	# Optionally include pressure normalized by inlet total pressure when available
	pt_in = simulation_result.settings_summary.get("boundary_conditions", {}).get("Pt_in") if simulation_result.settings_summary else None
	if pt_in is not None:
		series_map["pressure_over_total"] = tuple(p / float(pt_in) for p in simulation_result.gas_solution.pressure_values)

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


def generate_overlay_plots(
	labeled_results: list[tuple[str, SimulationResult]] | tuple[tuple[str, SimulationResult], ...],
	case_plots_directory: str | Path,
	overlay_series: dict[str, dict] | None = None,
) -> dict[str, str]:
	"""Generate overlay PNGs for multiple labelled simulation results.

	Parameters
	----------
	labeled_results:
		Iterable of (label, SimulationResult) tuples.
	case_plots_directory:
		Directory path where overlay PNGs will be written (plots/ under
		the case directory is recommended).

	Returns
	-------
	dict mapping plot_name -> written file path
	"""

	resolved_dir = Path(case_plots_directory)
	resolved_dir.mkdir(parents=True, exist_ok=True)

	# If the caller provided an overlay_series (as produced by
	# `extract_overlay_plot_series` in the GUI layer) use it directly so
	# disk-written overlays match the GUI's unit conversion, labels, and
	# titles. Otherwise, build a raw-SI series map from the SimulationResult
	# objects in `labeled_results` (legacy behaviour).
	series_map: dict[str, list[tuple[str, tuple[float, ...], tuple[float, ...]]]] = {}
	if overlay_series is not None:
		# overlay_series[field] -> {title, x_label, ylabel, series: [{label,x,y}, ...]}
		for field, data in overlay_series.items():
			for s in data.get("series", []):
				# ensure tuples
				x_vals = tuple(s.get("x", []))
				y_vals = tuple(s.get("y", []))
				label = s.get("label", "")
				series_map.setdefault(field, []).append((label, x_vals, y_vals))
	else:
		for label, sim in labeled_results:
			x_values = tuple(sim.gas_solution.x_values)
			per_run_map = {
				"pressure": tuple(sim.gas_solution.pressure_values),
				"temperature": tuple(sim.gas_solution.temperature_values),
				"working_fluid_velocity": tuple(sim.gas_solution.velocity_values),
				"droplet_velocity": tuple(sim.droplet_solution.velocity_values),
				"mach_number": tuple(sim.gas_solution.mach_number_values),
				"droplet_mean_diameter": tuple(sim.droplet_solution.mean_diameter_values),
				"droplet_maximum_diameter": tuple(sim.droplet_solution.maximum_diameter_values),
				"weber_number": tuple(sim.droplet_solution.weber_number_values),
				"area_profile": tuple(sim.gas_solution.area_values),
				"slip_velocity": tuple(sim.droplet_solution.slip_velocity_values),
			}
			pt_in = sim.settings_summary.get("boundary_conditions", {}).get("Pt_in") if sim.settings_summary else None
			if pt_in is not None:
				per_run_map["pressure_over_total"] = tuple(p / float(pt_in) for p in sim.gas_solution.pressure_values)

			for name, y_values in per_run_map.items():
				series_map.setdefault(name, []).append((label, x_values, y_values))

	written: dict[str, str] = {}
	try:
		for plot_name, series_list in series_map.items():
			# Skip empty series sets
			if not series_list:
				continue
			plot_path = resolved_dir / f"{plot_name}_overlay.png"
			# Match the GUI response rendering size so on-disk overlays are
			# byte-identical to figures rendered for the Graph tab.
			fig, ax = plt.subplots(figsize=(6.5, 3.5))
			for label, x_vals, y_vals in series_list:
				ax.plot(x_vals, y_vals, label=label)
			title, y_label = PLOT_LABELS.get(plot_name, (plot_name, ""))
			ax.set_xlabel("x [m]")
			ax.set_ylabel(y_label)
			ax.set_title(title)
			ax.grid(True)
			if len(series_list) > 1:
				ax.legend(fontsize="small")
			fig.tight_layout()
			fig.savefig(plot_path, bbox_inches="tight", dpi=96)
			# Also emit an alternate-capitalized filename for legacy GUI keys
			# (e.g. 'mach_number' -> 'Mach_number') so older code that
			# expects capitalized stems will find a matching PNG.
			parts = plot_name.split("_", 1)
			if parts:
				alt_key = parts[0].capitalize() + ("_" + parts[1] if len(parts) > 1 else "")
				alt_path = resolved_dir / f"{alt_key}_overlay.png"
				# write alt file only if it doesn't already exist
				if not alt_path.exists():
					fig.savefig(alt_path, bbox_inches="tight", dpi=96)
			plt.close(fig)
			written[plot_name] = str(plot_path)
	except OSError as exc:
		raise OutputError(f"Overlay plot generation failed for '{resolved_dir}': {exc}") from exc

	return written