"""Runtime application-service scaffold for startup-stage orchestration."""

from __future__ import annotations

from dataclasses import replace
from dataclasses import dataclass
from typing import Any, Callable

from supersonic_atomizer.breakup import BreakupModel, select_breakup_model
from supersonic_atomizer.common import OutputError, SupersonicAtomizerError
from supersonic_atomizer.config import (
	apply_config_defaults,
	load_raw_case_config,
	translate_case_config,
	validate_raw_config_schema,
	validate_semantic_config,
)
from supersonic_atomizer.domain import CaseConfig, ModelSelectionConfig, OutputMetadata, SimulationResult, ValidationReport
from supersonic_atomizer.io import (
	build_output_metadata,
	ensure_output_directories,
	write_simulation_result_csv,
	write_simulation_result_json,
)
from supersonic_atomizer.plotting import generate_profile_plots
from supersonic_atomizer.geometry import build_geometry_model
from supersonic_atomizer.geometry.geometry_model import GeometryModel
from supersonic_atomizer.solvers.droplet import solve_droplet_transport
from supersonic_atomizer.solvers.gas import solve_quasi_1d_gas_flow
from supersonic_atomizer.thermo import select_thermo_provider
from supersonic_atomizer.thermo.interfaces import ThermoProvider
from supersonic_atomizer.validation import validate_simulation_result

from .result_assembly import assemble_simulation_result


RawConfigLoader = Callable[[str], dict[str, Any]]
RawConfigTransformer = Callable[[dict[str, Any]], dict[str, Any]]
ConfigTranslator = Callable[[dict[str, Any]], CaseConfig]
GeometryBuilder = Callable[[Any], GeometryModel]
ThermoSelector = Callable[[CaseConfig], ThermoProvider]
BreakupSelector = Callable[[ModelSelectionConfig], BreakupModel]
GasSolver = Callable[..., Any]
DropletSolver = Callable[..., Any]
OutputMetadataBuilder = Callable[..., OutputMetadata]
OutputDirectoryInitializer = Callable[[OutputMetadata], None]
ResultAssembler = Callable[..., SimulationResult]
Validator = Callable[[SimulationResult], ValidationReport]
CsvWriter = Callable[[SimulationResult], str]
JsonWriter = Callable[[SimulationResult], str]
PlotGenerator = Callable[[SimulationResult], dict[str, str]]


@dataclass(frozen=True, slots=True)
class StartupDependencies:
	"""Startup-stage runtime dependencies built before solver execution."""

	case_config: CaseConfig
	geometry_model: GeometryModel
	thermo_provider: ThermoProvider


@dataclass(frozen=True, slots=True)
class StartupResult:
	"""Structured startup-stage result for success and failure paths."""

	status: str
	case_path: str
	startup_dependencies: StartupDependencies | None = None
	failure_category: str | None = None
	failure_message: str | None = None


@dataclass(frozen=True, slots=True)
class SimulationRunResult:
	"""Structured full-run result for success and failure paths."""

	status: str
	case_path: str
	simulation_result: SimulationResult | None = None
	failure_category: str | None = None
	failure_message: str | None = None
	failure_stage: str | None = None


@dataclass(frozen=True, slots=True)
class ApplicationService:
	"""Injected application boundary for config and startup dependency orchestration."""

	raw_config_loader: RawConfigLoader
	defaults_applier: RawConfigTransformer
	raw_config_validator: RawConfigTransformer
	semantic_validator: RawConfigTransformer
	config_translator: ConfigTranslator
	geometry_builder: GeometryBuilder
	thermo_selector: ThermoSelector
	breakup_selector: BreakupSelector = select_breakup_model
	gas_solver: GasSolver = solve_quasi_1d_gas_flow
	droplet_solver: DropletSolver = solve_droplet_transport
	output_metadata_builder: OutputMetadataBuilder = build_output_metadata
	output_directory_initializer: OutputDirectoryInitializer = ensure_output_directories
	result_assembler: ResultAssembler = assemble_simulation_result
	validator: Validator = validate_simulation_result
	csv_writer: CsvWriter = write_simulation_result_csv
	json_writer: JsonWriter = write_simulation_result_json
	plot_generator: PlotGenerator = generate_profile_plots

	def run_startup(self, case_path: str) -> StartupResult:
		"""Execute the pre-solver startup flow and return structured status."""

		try:
			raw_config = self.raw_config_loader(case_path)
			validated_schema_config = self.raw_config_validator(raw_config)
			validated_semantic_config = self.semantic_validator(validated_schema_config)
			normalized_config = self.defaults_applier(validated_semantic_config)
			case_config = self.config_translator(normalized_config)
			geometry_model = self.geometry_builder(case_config.geometry)
			thermo_provider = self.thermo_selector(case_config)

			return StartupResult(
				status="ready",
				case_path=case_path,
				startup_dependencies=StartupDependencies(
					case_config=case_config,
					geometry_model=geometry_model,
					thermo_provider=thermo_provider,
				),
			)
		except SupersonicAtomizerError as exc:
			return StartupResult(
				status="failed",
				case_path=case_path,
				failure_category=type(exc).__name__,
				failure_message=str(exc),
			)
		except (FileNotFoundError, ValueError) as exc:
			return StartupResult(
				status="failed",
				case_path=case_path,
				failure_category=type(exc).__name__,
				failure_message=str(exc),
			)

	def run_simulation(self, case_path: str) -> SimulationRunResult:
		"""Execute the supported full MVP runtime workflow and return structured status."""

		startup_result = self.run_startup(case_path)
		if startup_result.status != "ready" or startup_result.startup_dependencies is None:
			return SimulationRunResult(
				status="failed",
				case_path=case_path,
				failure_category=startup_result.failure_category,
				failure_message=startup_result.failure_message,
				failure_stage="startup",
			)

		startup_dependencies = startup_result.startup_dependencies
		simulation_result: SimulationResult | None = None

		try:
			breakup_model = self.breakup_selector(startup_dependencies.case_config.models)
			gas_solution = self.gas_solver(
				geometry_model=startup_dependencies.geometry_model,
				boundary_conditions=startup_dependencies.case_config.boundary_conditions,
				thermo_provider=startup_dependencies.thermo_provider,
			)
			droplet_solution = self.droplet_solver(
				gas_solution=gas_solution,
				injection_config=startup_dependencies.case_config.droplet_injection,
				breakup_model=breakup_model,
			)
			output_metadata = self.output_metadata_builder(
				output_config=startup_dependencies.case_config.outputs,
			)
			self.output_directory_initializer(output_metadata)
			simulation_result = self.result_assembler(
				case_config=startup_dependencies.case_config,
				gas_solution=gas_solution,
				droplet_solution=droplet_solution,
				output_metadata=output_metadata,
			)
			validation_report = self.validator(simulation_result)
			simulation_result = replace(simulation_result, validation_report=validation_report)

			if simulation_result.output_metadata is not None:
				if simulation_result.output_metadata.write_csv:
					self.csv_writer(simulation_result)
				if simulation_result.output_metadata.write_json:
					self.json_writer(simulation_result)
				if simulation_result.output_metadata.generate_plots:
					self.plot_generator(simulation_result)

			return SimulationRunResult(
				status="completed",
				case_path=case_path,
				simulation_result=simulation_result,
			)
		except OutputError as exc:
			return SimulationRunResult(
				status="output-failed",
				case_path=case_path,
				simulation_result=simulation_result,
				failure_category=type(exc).__name__,
				failure_message=str(exc),
				failure_stage="outputs",
			)
		except SupersonicAtomizerError as exc:
			return SimulationRunResult(
				status="failed",
				case_path=case_path,
				simulation_result=simulation_result,
				failure_category=type(exc).__name__,
				failure_message=str(exc),
				failure_stage="simulation",
			)


def create_application_service() -> ApplicationService:
	"""Create the default application-service scaffold for later startup orchestration."""

	return ApplicationService(
		raw_config_loader=load_raw_case_config,
		defaults_applier=apply_config_defaults,
		raw_config_validator=validate_raw_config_schema,
		semantic_validator=validate_semantic_config,
		config_translator=translate_case_config,
		geometry_builder=build_geometry_model,
		thermo_selector=select_thermo_provider,
	)