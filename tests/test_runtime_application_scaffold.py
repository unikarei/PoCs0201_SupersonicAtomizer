from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.app import (
	ApplicationService,
	StartupResult,
	create_application_service,
	get_application_service,
)
from supersonic_atomizer.common import ConfigurationError
from supersonic_atomizer.config import (
	apply_config_defaults,
	load_raw_case_config,
	translate_case_config,
	validate_raw_config_schema,
	validate_semantic_config,
)
from supersonic_atomizer.geometry import build_geometry_model
from supersonic_atomizer.thermo import select_thermo_provider


class TestRuntimeApplicationScaffold(unittest.TestCase):
	def test_application_service_factory_returns_runtime_service(self) -> None:
		service = create_application_service()

		self.assertIsInstance(service, ApplicationService)
		self.assertIs(service.raw_config_loader, load_raw_case_config)
		self.assertIs(service.defaults_applier, apply_config_defaults)
		self.assertIs(service.raw_config_validator, validate_raw_config_schema)
		self.assertIs(service.semantic_validator, validate_semantic_config)
		self.assertIs(service.config_translator, translate_case_config)
		self.assertIs(service.geometry_builder, build_geometry_model)
		self.assertIs(service.thermo_selector, select_thermo_provider)

	def test_application_entry_point_returns_default_service(self) -> None:
		service = get_application_service()

		self.assertIsInstance(service, ApplicationService)
		self.assertIs(service.raw_config_loader, load_raw_case_config)
		self.assertIs(service.thermo_selector, select_thermo_provider)

	def test_run_startup_returns_structured_success_status(self) -> None:
		service = create_application_service()
		case_yaml = """
fluid:
  working_fluid: air
boundary_conditions:
  Pt_in: 500000.0
  Tt_in: 450.0
  Ps_out: 100000.0
geometry:
  x_start: 0.0
  x_end: 0.1
  n_cells: 10
  area_distribution:
    type: table
    x: [0.0, 0.1]
    A: [0.0001, 0.00012]
droplet_injection:
  droplet_velocity_in: 10.0
  droplet_diameter_mean_in: 0.0001
  droplet_diameter_max_in: 0.0002
""".strip()

		with tempfile.TemporaryDirectory() as temporary_directory:
			case_path = Path(temporary_directory) / "case.yaml"
			case_path.write_text(case_yaml, encoding="utf-8")

			startup_result = service.run_startup(str(case_path))

		self.assertIsInstance(startup_result, StartupResult)
		self.assertEqual(startup_result.status, "ready")
		self.assertEqual(startup_result.case_path, str(case_path))
		self.assertIsNotNone(startup_result.startup_dependencies)
		self.assertIsNone(startup_result.failure_category)
		self.assertEqual(
			startup_result.startup_dependencies.case_config.fluid.working_fluid,
			"air",
		)

	def test_run_startup_returns_structured_failure_status(self) -> None:
		def failing_loader(_: str) -> dict[str, object]:
			return {}

		def passthrough_transform(config: dict[str, object]) -> dict[str, object]:
			return config

		def failing_semantic_validator(_: dict[str, object]) -> dict[str, object]:
			raise ConfigurationError("startup semantic validation failed")

		service = ApplicationService(
			raw_config_loader=failing_loader,
			defaults_applier=passthrough_transform,
			raw_config_validator=passthrough_transform,
			semantic_validator=failing_semantic_validator,
			config_translator=translate_case_config,
			geometry_builder=build_geometry_model,
			thermo_selector=select_thermo_provider,
		)

		startup_result = service.run_startup("failing-case.yaml")

		self.assertEqual(startup_result.status, "failed")
		self.assertEqual(startup_result.case_path, "failing-case.yaml")
		self.assertIsNone(startup_result.startup_dependencies)
		self.assertEqual(startup_result.failure_category, "ConfigurationError")
		self.assertEqual(startup_result.failure_message, "startup semantic validation failed")


if __name__ == "__main__":
	unittest.main()