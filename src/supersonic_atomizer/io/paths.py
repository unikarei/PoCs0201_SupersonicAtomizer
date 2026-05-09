"""Runtime output-path and artifact-metadata helpers."""

from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path
import shutil

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
	"area_profile": "area_profile.png",
	"slip_velocity": "slip_velocity.png",
	"pressure_over_total": "pressure_over_total.png",
}


def _generate_run_id() -> str:
	"""Return a filesystem-safe default run identifier."""

	# Include microseconds so rapid consecutive runs do not collide.
	return datetime.now(UTC).strftime("run-%Y%m%dT%H%M%S%fZ")


def build_output_metadata(*, output_config: OutputConfig, run_id: str | None = None, project: str | None = None, case_name: str | None = None) -> OutputMetadata:
	"""Build structured artifact metadata following the approved conventions."""

	resolved_run_id = run_id or _generate_run_id()
	if not resolved_run_id.strip():
		raise OutputError("Output metadata requires a non-empty run identifier.")

	# Prefer organizing outputs under project/case when provided to mirror cases/ layout
	base = Path(output_config.output_directory)
	if project and case_name:
		run_directory = base / project / case_name / resolved_run_id
	else:
		run_directory = base / resolved_run_id
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
		clean_case=getattr(output_config, "clean_case", True),
	)


def ensure_output_directories(output_metadata: OutputMetadata) -> None:
	"""Create the runtime output directories required by the artifact metadata.

	Before creating the new run directory, remove any existing files and
	subdirectories under the case directory so only the fresh run results
	remain. This implements the requested behaviour to clear
	`output/project/case/` prior to writing the new run.
	"""

	try:
		# Determine run and case directories
		run_dir = Path(output_metadata.output_directory)
		case_dir = run_dir.parent

		# If requested via OutputMetadata.clean_case, remove all existing
		# children under the case directory so that the upcoming run
		# directory is the only content. When False, preserve
		# previous run directories to allow multi-run overlays to be
		# generated and stored.
		if getattr(output_metadata, "clean_case", False):
			if case_dir.exists() and case_dir.is_dir():
				for child in case_dir.iterdir():
					try:
						if child.resolve() == run_dir.resolve():
							continue
					except OSError:
						pass
					try:
						if child.is_file() or child.is_symlink():
							child.unlink()
						elif child.is_dir():
							shutil.rmtree(child)
					except OSError:
						pass

		# Create the run directory and plots directory as required.
		run_dir.mkdir(parents=True, exist_ok=True)
		if output_metadata.plot_paths:
			Path(next(iter(output_metadata.plot_paths.values()))).parent.mkdir(parents=True, exist_ok=True)
	except OSError as exc:
		raise OutputError(f"Failed to create output directories for '{output_metadata.output_directory}': {exc}") from exc


def prune_old_output_runs(output_metadata: OutputMetadata) -> None:
	"""Remove older run directories leaving only the current run directory.

	This function looks at the parent directory containing per-run subdirectories
	and removes siblings that match the run- prefix except for the active run.
	Be conservative: only remove directories whose names start with "run-".
	"""
	try:
		current = Path(output_metadata.output_directory)
		parent = current.parent
		if not parent.is_dir():
			return
		for child in parent.iterdir():
			if child == current:
				continue
			if child.is_dir() and child.name.startswith("run-"):
				# remove directory tree
				for sub in child.rglob("*"):
					if sub.is_file():
						sub.unlink()
					for sub in reversed(list(child.rglob("*"))):
						try:
							if sub.is_dir():
								sub.rmdir()
						except OSError:
							pass
				try:
					child.rmdir()
				except OSError:
					# best-effort cleanup; ignore failures
					pass
	except OSError:
		# Do not raise in cleanup — it's non-critical
		pass