"""Runtime application-service scaffold for startup-stage orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from supersonic_atomizer.common import SupersonicAtomizerError
from supersonic_atomizer.config import (
	apply_config_defaults,
	load_raw_case_config,
	translate_case_config,
	validate_raw_config_schema,
	validate_semantic_config,
)
from supersonic_atomizer.domain import CaseConfig
from supersonic_atomizer.geometry import build_geometry_model
from supersonic_atomizer.geometry.geometry_model import GeometryModel
from supersonic_atomizer.thermo import select_thermo_provider
from supersonic_atomizer.thermo.interfaces import ThermoProvider


RawConfigLoader = Callable[[str], dict[str, Any]]
RawConfigTransformer = Callable[[dict[str, Any]], dict[str, Any]]
ConfigTranslator = Callable[[dict[str, Any]], CaseConfig]
GeometryBuilder = Callable[[Any], GeometryModel]
ThermoSelector = Callable[[CaseConfig], ThermoProvider]


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
class ApplicationService:
	"""Injected application boundary for config and startup dependency orchestration."""

	raw_config_loader: RawConfigLoader
	defaults_applier: RawConfigTransformer
	raw_config_validator: RawConfigTransformer
	semantic_validator: RawConfigTransformer
	config_translator: ConfigTranslator
	geometry_builder: GeometryBuilder
	thermo_selector: ThermoSelector

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