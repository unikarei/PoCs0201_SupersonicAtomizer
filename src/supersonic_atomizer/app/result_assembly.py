"""Runtime simulation-result assembly helpers."""

from __future__ import annotations

from supersonic_atomizer.common import NumericalError
from supersonic_atomizer.domain import (
	CaseConfig,
	DropletSolution,
	GasSolution,
	OutputMetadata,
	RunDiagnostics,
	SimulationResult,
	ValidationReport,
)


def _merge_run_status(*statuses: str) -> str:
	"""Return a conservative merged run status for assembled results."""

	normalized_statuses = tuple(status.lower() for status in statuses)
	if any(status in {"failed", "error"} for status in normalized_statuses):
		return "failed"
	if any(status in {"warning", "warn"} for status in normalized_statuses):
		return "warning"
	if all(status == "completed" for status in normalized_statuses):
		return "completed"
	return normalized_statuses[-1]


def _build_settings_summary(case_config: CaseConfig) -> dict[str, object]:
	"""Return a machine-readable settings summary from the validated case config."""

	return {
		"fluid": {
			"working_fluid": case_config.fluid.working_fluid,
			"inlet_wetness": case_config.fluid.inlet_wetness,
		},
		"boundary_conditions": {
			"Pt_in": case_config.boundary_conditions.Pt_in,
			"Tt_in": case_config.boundary_conditions.Tt_in,
			"Ps_out": case_config.boundary_conditions.Ps_out,
		},
		"models": {
			"drag_model": case_config.models.drag_model,
			"breakup_model": case_config.models.breakup_model,
			"critical_weber_number": case_config.models.critical_weber_number,
			"breakup_factor_mean": case_config.models.breakup_factor_mean,
			"breakup_factor_max": case_config.models.breakup_factor_max,
			"steam_property_model": case_config.models.steam_property_model,
		},
		"outputs": {
			"output_directory": case_config.outputs.output_directory,
			"write_csv": case_config.outputs.write_csv,
			"write_json": case_config.outputs.write_json,
			"generate_plots": case_config.outputs.generate_plots,
		},
	}


def assemble_simulation_result(
	*,
	case_config: CaseConfig,
	gas_solution: GasSolution,
	droplet_solution: DropletSolution,
	output_metadata: OutputMetadata | None = None,
	validation_report: ValidationReport | None = None,
) -> SimulationResult:
	"""Assemble structured runtime results from aligned gas and droplet outputs."""

	if len(gas_solution.states) != len(droplet_solution.states):
		raise NumericalError(
			"Simulation-result assembly requires gas and droplet solutions with matching axial lengths."
		)
	if gas_solution.x_values != droplet_solution.x_values:
		raise NumericalError(
			"Simulation-result assembly requires gas and droplet solutions aligned on the same axial coordinates."
		)

	gas_diagnostics = gas_solution.diagnostics or RunDiagnostics(status="completed")
	droplet_diagnostics = droplet_solution.diagnostics or RunDiagnostics(status="completed")
	merged_diagnostics = RunDiagnostics(
		status=_merge_run_status(gas_diagnostics.status, droplet_diagnostics.status),
		warnings=gas_diagnostics.warnings + droplet_diagnostics.warnings,
		messages=(
			gas_diagnostics.messages
			+ droplet_diagnostics.messages
			+ ("Simulation result assembled from aligned gas and droplet solutions.",)
		),
		failure_category=gas_diagnostics.failure_category or droplet_diagnostics.failure_category,
		failure_location=gas_diagnostics.failure_location or droplet_diagnostics.failure_location,
		last_valid_state_summary=(
			gas_diagnostics.last_valid_state_summary or droplet_diagnostics.last_valid_state_summary
		),
	)

	return SimulationResult(
		case_name=case_config.case_name,
		working_fluid=case_config.fluid.working_fluid,
		gas_solution=gas_solution,
		droplet_solution=droplet_solution,
		diagnostics=merged_diagnostics,
		settings_summary=_build_settings_summary(case_config),
		validation_report=validation_report,
		output_metadata=output_metadata,
	)