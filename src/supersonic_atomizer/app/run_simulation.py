"""Application entry-point scaffolding for later runtime execution flow."""

from __future__ import annotations

from supersonic_atomizer.app.laval_nozzle_sweep import LavalSweepResult, run_laval_nozzle_back_pressure_sweep
from supersonic_atomizer.app.services import (
	ApplicationService,
	SimulationRunResult,
	StartupResult,
	create_application_service,
)


def get_application_service() -> ApplicationService:
	"""Return the default application-service boundary for runtime orchestration."""

	return create_application_service()


def run_startup(case_path: str) -> StartupResult:
	"""Run the startup-stage application flow using the default service."""

	return get_application_service().run_startup(case_path)


def run_simulation(case_path: str) -> SimulationRunResult:
	"""Run the supported full application workflow using the default service."""

	return get_application_service().run_simulation(case_path)


def run_laval_sweep(case_path: str, *, output_directory: str | None = None) -> LavalSweepResult:
	"""Run the Laval-nozzle internal-flow back-pressure sweep utility."""

	return run_laval_nozzle_back_pressure_sweep(
		case_path=case_path,
		output_directory=output_directory,
	)