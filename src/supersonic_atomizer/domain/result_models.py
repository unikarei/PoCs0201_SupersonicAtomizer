"""Runtime result and diagnostics models.

These models aggregate solver outputs, diagnostics, validation summaries, and
artifact metadata. They must remain free of solver computations and writer
implementation details.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .state_models import DropletSolution, GasSolution


@dataclass(frozen=True, slots=True)
class RunDiagnostics:
	"""Structured diagnostics for one simulation run."""

	status: str
	warnings: tuple[str, ...] = field(default_factory=tuple)
	messages: tuple[str, ...] = field(default_factory=tuple)
	failure_category: str | None = None
	failure_location: str | None = None
	last_valid_state_summary: str | None = None


@dataclass(frozen=True, slots=True)
class ValidationReport:
	"""Structured validation summary for one simulation run."""

	status: str
	checks_run: int = 0
	checks_passed: int = 0
	checks_warned: int = 0
	checks_failed: int = 0
	observations: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class OutputMetadata:
	"""Structured output artifact metadata and traceability."""

	run_id: str
	output_directory: str
	csv_path: str | None = None
	json_path: str | None = None
	diagnostics_path: str | None = None
	plot_paths: dict[str, str] = field(default_factory=dict)
	write_csv: bool = True
	write_json: bool = True
	generate_plots: bool = True


@dataclass(frozen=True, slots=True)
class SimulationResult:
	"""Top-level simulation result consumed by downstream layers."""

	case_name: str | None
	working_fluid: str
	gas_solution: GasSolution
	droplet_solution: DropletSolution
	diagnostics: RunDiagnostics
	validation_report: ValidationReport | None = None
	output_metadata: OutputMetadata | None = None