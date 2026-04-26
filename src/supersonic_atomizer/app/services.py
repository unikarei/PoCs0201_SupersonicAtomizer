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
from supersonic_atomizer.domain import GasSolution, GasState, ThermoState
from supersonic_atomizer.io import (
	build_output_metadata,
	ensure_output_directories,
	write_simulation_result_csv,
	write_simulation_result_json,
)
from supersonic_atomizer.plotting import generate_profile_plots
from supersonic_atomizer.geometry import build_geometry_model
from supersonic_atomizer.geometry.geometry_model import GeometryModel
from supersonic_atomizer.solvers.droplet import DragModel, select_drag_model, solve_droplet_transport
from supersonic_atomizer.solvers.gas import apply_coupling_source_terms, solve_quasi_1d_gas_flow
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
DragSelector = Callable[[ModelSelectionConfig], DragModel]
GasSolver = Callable[..., Any]
DropletSolver = Callable[..., Any]
OutputMetadataBuilder = Callable[..., OutputMetadata]
OutputDirectoryInitializer = Callable[[OutputMetadata], None]
ResultAssembler = Callable[..., SimulationResult]
Validator = Callable[[SimulationResult], ValidationReport]
CsvWriter = Callable[[SimulationResult], str]
JsonWriter = Callable[[SimulationResult], str]
PlotGenerator = Callable[[SimulationResult], dict[str, str]]


def _safe_abs(value: float) -> float:
	return abs(float(value))


def _mean_absolute_difference(left: tuple[float, ...], right: tuple[float, ...]) -> float:
	if len(left) != len(right) or not left:
		return float("inf")
	return sum(abs(a - b) for a, b in zip(left, right, strict=False)) / len(left)


def _estimate_mass_loading(case_config: CaseConfig, gas_solution: GasSolution) -> float:
	"""Return scalar mass-loading estimate phi = m_liq / m_gas at inlet.

	This is a reduced-order estimate used by the two-way approximation mode.
	"""

	water_mass_flow_rate = case_config.droplet_injection.water_mass_flow_rate
	if water_mass_flow_rate is None:
		return 0.0

	inlet_state = gas_solution.states[0]
	gas_mass_flow_rate = _safe_abs(inlet_state.density * inlet_state.velocity * inlet_state.area)
	if gas_mass_flow_rate <= 1.0e-12:
		return 0.0

	return _safe_abs(water_mass_flow_rate) / gas_mass_flow_rate


def _estimate_mean_slip_ratio(gas_solution: GasSolution, droplet_solution: Any) -> float:
	if not gas_solution.velocity_values or not droplet_solution.slip_velocity_values:
		return 0.0

	ratios: list[float] = []
	for gas_velocity, slip_velocity in zip(
		gas_solution.velocity_values,
		droplet_solution.slip_velocity_values,
		strict=False,
	):
		denominator = max(_safe_abs(gas_velocity), 1.0e-9)
		ratios.append(_safe_abs(slip_velocity) / denominator)

	if not ratios:
		return 0.0
	return sum(ratios) / len(ratios)


def _scaled_thermo_state(base: ThermoState, density_scale: float) -> ThermoState:
	return ThermoState(
		pressure=base.pressure,
		temperature=base.temperature,
		density=base.density * density_scale,
		enthalpy=base.enthalpy,
		sound_speed=base.sound_speed,
		dynamic_viscosity=base.dynamic_viscosity,
	)


def _apply_feedback_to_gas_solution(
	base_gas_solution: GasSolution,
	*,
	velocity_scale: float,
) -> GasSolution:
	"""Build a gas-solution variant with reduced velocity and adjusted density.

	The scaling keeps the same pressure/temperature branch but applies a compact
	feedback correction for two-way approximation mode.
	"""

	if velocity_scale <= 0.0:
		raise ValueError("velocity_scale must be positive.")

	density_scale = 1.0 / velocity_scale
	updated_states: list[GasState] = []
	pressure_values: list[float] = []
	temperature_values: list[float] = []
	density_values: list[float] = []
	velocity_values: list[float] = []
	mach_values: list[float] = []

	for state in base_gas_solution.states:
		updated_velocity = state.velocity * velocity_scale
		updated_thermo = _scaled_thermo_state(state.thermo_state, density_scale=density_scale)
		updated_state = GasState(
			x=state.x,
			area=state.area,
			pressure=state.pressure,
			temperature=state.temperature,
			density=updated_thermo.density,
			velocity=updated_velocity,
			mach_number=state.mach_number * velocity_scale,
			thermo_state=updated_thermo,
		)
		updated_states.append(updated_state)
		pressure_values.append(updated_state.pressure)
		temperature_values.append(updated_state.temperature)
		density_values.append(updated_state.density)
		velocity_values.append(updated_state.velocity)
		mach_values.append(updated_state.mach_number)

	return GasSolution(
		states=tuple(updated_states),
		x_values=base_gas_solution.x_values,
		area_values=base_gas_solution.area_values,
		pressure_values=tuple(pressure_values),
		temperature_values=tuple(temperature_values),
		density_values=tuple(density_values),
		velocity_values=tuple(velocity_values),
		mach_number_values=tuple(mach_values),
		diagnostics=base_gas_solution.diagnostics,
	)


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
	drag_selector: DragSelector = select_drag_model

	def _run_one_way_solve(self, startup_dependencies: StartupDependencies, breakup_model: BreakupModel) -> tuple[GasSolution, Any]:
		drag_model = self.drag_selector(startup_dependencies.case_config.models)
		model_settings = startup_dependencies.case_config.models
		gas_solution = self.gas_solver(
			geometry_model=startup_dependencies.geometry_model,
			boundary_conditions=startup_dependencies.case_config.boundary_conditions,
			thermo_provider=startup_dependencies.thermo_provider,
			gas_solver_mode=model_settings.gas_solver_mode,
		)
		droplet_solution = self.droplet_solver(
			gas_solution=gas_solution,
			injection_config=startup_dependencies.case_config.droplet_injection,
			drag_model=drag_model,
			breakup_model=breakup_model,
			distribution_model=model_settings.droplet_distribution_model,
			distribution_sigma=model_settings.droplet_distribution_sigma,
		)
		return gas_solution, droplet_solution

	def _run_two_way_approx_solve(self, startup_dependencies: StartupDependencies, breakup_model: BreakupModel) -> tuple[GasSolution, Any]:
		"""Run a reduced-order two-way approximation loop.

		This mode preserves the existing gas solver and applies iterative feedback
		corrections in the orchestration layer.
		"""

		model_settings = startup_dependencies.case_config.models
		base_gas_solution = self.gas_solver(
			geometry_model=startup_dependencies.geometry_model,
			boundary_conditions=startup_dependencies.case_config.boundary_conditions,
			thermo_provider=startup_dependencies.thermo_provider,
			gas_solver_mode=model_settings.gas_solver_mode,
		)

		drag_model = self.drag_selector(startup_dependencies.case_config.models)

		mass_loading = _estimate_mass_loading(startup_dependencies.case_config, base_gas_solution)
		relaxation = model_settings.two_way_feedback_relaxation
		max_iterations = model_settings.two_way_max_iterations

		gas_solution = base_gas_solution
		droplet_solution = self.droplet_solver(
			gas_solution=gas_solution,
			injection_config=startup_dependencies.case_config.droplet_injection,
			drag_model=drag_model,
			breakup_model=breakup_model,
			distribution_model=model_settings.droplet_distribution_model,
			distribution_sigma=model_settings.droplet_distribution_sigma,
		)

		previous_velocity_scale = 1.0
		for _ in range(max_iterations):
			slip_ratio = _estimate_mean_slip_ratio(gas_solution, droplet_solution)
			feedback_strength = min(0.9, mass_loading * slip_ratio * relaxation)
			velocity_scale = max(0.1, 1.0 - feedback_strength)

			gas_solution = _apply_feedback_to_gas_solution(
				base_gas_solution,
				velocity_scale=velocity_scale,
			)
			droplet_solution = self.droplet_solver(
				gas_solution=gas_solution,
				injection_config=startup_dependencies.case_config.droplet_injection,
				drag_model=drag_model,
				breakup_model=breakup_model,
				distribution_model=model_settings.droplet_distribution_model,
				distribution_sigma=model_settings.droplet_distribution_sigma,
			)

			if abs(velocity_scale - previous_velocity_scale) < 1.0e-3:
				break
			previous_velocity_scale = velocity_scale

		return gas_solution, droplet_solution

	def _run_two_way_coupled_solve(self, startup_dependencies: StartupDependencies, breakup_model: BreakupModel) -> tuple[GasSolution, Any]:
		"""Run operator-split two-way coupling with source-term feedback iterations."""

		model_settings = startup_dependencies.case_config.models
		drag_model = self.drag_selector(model_settings)
		max_iterations = model_settings.two_way_max_iterations
		relaxation = model_settings.two_way_feedback_relaxation
		tolerance = model_settings.two_way_convergence_tolerance

		coupling_source_terms = None
		gas_solution = self.gas_solver(
			geometry_model=startup_dependencies.geometry_model,
			boundary_conditions=startup_dependencies.case_config.boundary_conditions,
			thermo_provider=startup_dependencies.thermo_provider,
			gas_solver_mode=model_settings.gas_solver_mode,
		)
		droplet_solution = self.droplet_solver(
			gas_solution=gas_solution,
			injection_config=startup_dependencies.case_config.droplet_injection,
			drag_model=drag_model,
			breakup_model=breakup_model,
			distribution_model=model_settings.droplet_distribution_model,
			distribution_sigma=model_settings.droplet_distribution_sigma,
		)

		converged = False
		iteration_count = 1
		for iteration in range(max_iterations):
			base_gas_solution = self.gas_solver(
				geometry_model=startup_dependencies.geometry_model,
				boundary_conditions=startup_dependencies.case_config.boundary_conditions,
				thermo_provider=startup_dependencies.thermo_provider,
				gas_solver_mode=model_settings.gas_solver_mode,
			)
			if coupling_source_terms is not None:
				gas_solution = apply_coupling_source_terms(
					base_gas_solution=base_gas_solution,
					coupling_source_terms=coupling_source_terms,
					relaxation=relaxation,
				)
			else:
				gas_solution = base_gas_solution

			droplet_solution = self.droplet_solver(
				gas_solution=gas_solution,
				injection_config=startup_dependencies.case_config.droplet_injection,
				drag_model=drag_model,
				breakup_model=breakup_model,
				distribution_model=model_settings.droplet_distribution_model,
				distribution_sigma=model_settings.droplet_distribution_sigma,
			)
			next_source_terms = droplet_solution.coupling_source_terms
			iteration_count = iteration + 1

			if coupling_source_terms is not None and next_source_terms is not None:
				residual = _mean_absolute_difference(
					coupling_source_terms.momentum_source_values,
					next_source_terms.momentum_source_values,
				)
				if residual <= tolerance:
					converged = True
					coupling_source_terms = next_source_terms
					break

			coupling_source_terms = next_source_terms

		if gas_solution.diagnostics is not None:
			gas_solution = replace(
				gas_solution,
				diagnostics=replace(
					gas_solution.diagnostics,
					messages=(
						gas_solution.diagnostics.messages
						+ (
							"coupling_mode=two_way_coupled",
							f"coupling_iterations={iteration_count}",
							f"coupling_converged={converged}",
						)
					),
				),
			)

		if droplet_solution.diagnostics is not None:
			droplet_solution = replace(
				droplet_solution,
				diagnostics=replace(
					droplet_solution.diagnostics,
					messages=(
						droplet_solution.diagnostics.messages
						+ (
							"coupling_mode=two_way_coupled",
							f"coupling_iterations={iteration_count}",
							f"coupling_converged={converged}",
						)
					),
				),
			)

		return gas_solution, droplet_solution

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

			coupling_mode = startup_dependencies.case_config.models.coupling_mode
			if coupling_mode == "two_way_approx":
				gas_solution, droplet_solution = self._run_two_way_approx_solve(
					startup_dependencies,
					breakup_model,
				)
			elif coupling_mode == "two_way_coupled":
				gas_solution, droplet_solution = self._run_two_way_coupled_solve(
					startup_dependencies,
					breakup_model,
				)
			else:
				gas_solution, droplet_solution = self._run_one_way_solve(
					startup_dependencies,
					breakup_model,
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