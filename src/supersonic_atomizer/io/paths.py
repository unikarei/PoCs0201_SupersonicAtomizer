"""Runtime output-path and artifact-metadata helpers."""

from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path

from supersonic_atomizer.common import OutputError
from supersonic_atomizer.domain import OutputMetadata, OutputConfig


PLOT_FILENAMES: dict[str, str] = {
	"pressure": "pressure.png",
	"temperature": "temperature.png",
	"working_fluid_velocity": "working_fluid_velocity.png",
	"droplet_velocity": "droplet_velocity.png",
	"mach_number": "mach_number.png",
	"droplet_mean_diameter": "droplet_mean_diameter.png",
	"droplet_maximum_diameter": "droplet_maximum_diameter.png",
	"weber_number": "weber_number.png",
}


def _generate_run_id() -> str:
	"""Return a filesystem-safe default run identifier."""

	return datetime.now(UTC).strftime("run-%Y%m%dT%H%M%SZ")


def build_output_metadata(*, output_config: OutputConfig, run_id: str | None = None) -> OutputMetadata:
	"""Build structured artifact metadata following the approved conventions."""

	resolved_run_id = run_id or _generate_run_id()
	if not resolved_run_id.strip():
		raise OutputError("Output metadata requires a non-empty run identifier.")

	run_directory = Path(output_config.output_directory) / resolved_run_id
	plot_paths = {
		plot_name: str(run_directory / "plots" / filename)
		for plot_name, filename in PLOT_FILENAMES.items()
	} if output_config.generate_plots else {}

	return OutputMetadata(
		run_id=resolved_run_id,
		output_directory=str(run_directory),
		csv_path=str(run_directory / "results.csv") if output_config.write_csv else None,
		json_path=str(run_directory / "results.json") if output_config.write_json else None,
		diagnostics_path=str(run_directory / "diagnostics.json"),
		plot_paths=plot_paths,
		write_csv=output_config.write_csv,
		write_json=output_config.write_json,
		generate_plots=output_config.generate_plots,
	)


def ensure_output_directories(output_metadata: OutputMetadata) -> None:
	"""Create the runtime output directories required by the artifact metadata."""

	try:
		Path(output_metadata.output_directory).mkdir(parents=True, exist_ok=True)
		if output_metadata.plot_paths:
			Path(next(iter(output_metadata.plot_paths.values()))).parent.mkdir(parents=True, exist_ok=True)
	except OSError as exc:
		raise OutputError(f"Failed to create output directories for '{output_metadata.output_directory}': {exc}") from exc