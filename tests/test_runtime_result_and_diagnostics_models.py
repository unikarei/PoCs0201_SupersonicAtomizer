from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.domain import (
	DropletSolution,
	DropletState,
	GasSolution,
	GasState,
	OutputMetadata,
	RunDiagnostics,
	SimulationResult,
	ThermoState,
	ValidationReport,
)


def _make_gas_solution() -> GasSolution:
	thermo_state = ThermoState(
		pressure=100000.0,
		temperature=500.0,
		density=0.7,
		enthalpy=450000.0,
		sound_speed=420.0,
	)
	gas_state = GasState(
		x=0.0,
		area=1.0e-4,
		pressure=100000.0,
		temperature=500.0,
		density=0.7,
		velocity=250.0,
		mach_number=0.6,
		thermo_state=thermo_state,
	)
	return GasSolution(
		states=(gas_state,),
		x_values=(0.0,),
		area_values=(1.0e-4,),
		pressure_values=(100000.0,),
		temperature_values=(500.0,),
		density_values=(0.7,),
		velocity_values=(250.0,),
		mach_number_values=(0.6,),
	)


def _make_droplet_solution() -> DropletSolution:
	droplet_state = DropletState(
		x=0.0,
		velocity=10.0,
		slip_velocity=240.0,
		mean_diameter=1.0e-4,
		maximum_diameter=3.0e-4,
		weber_number=12.0,
		reynolds_number=250.0,
		breakup_triggered=False,
	)
	return DropletSolution(
		states=(droplet_state,),
		x_values=(0.0,),
		velocity_values=(10.0,),
		slip_velocity_values=(240.0,),
		mean_diameter_values=(1.0e-4,),
		maximum_diameter_values=(3.0e-4,),
		weber_number_values=(12.0,),
		reynolds_number_values=(250.0,),
		breakup_flags=(False,),
	)


class TestRuntimeResultAndDiagnosticsModels(unittest.TestCase):
	def test_constructs_result_and_diagnostics_models(self) -> None:
		diagnostics = RunDiagnostics(
			status="success",
			warnings=("minor warning",),
			messages=("run completed",),
		)
		validation = ValidationReport(
			status="pass",
			checks_run=2,
			checks_passed=2,
			checks_warned=0,
			checks_failed=0,
			observations=("trend looks correct",),
		)
		output_metadata = OutputMetadata(
			run_id="run-001",
			output_directory="outputs/run-001",
			csv_path="outputs/run-001/results.csv",
			json_path="outputs/run-001/results.json",
			diagnostics_path="outputs/run-001/diagnostics.json",
			plot_paths={"pressure": "outputs/run-001/pressure.png"},
			write_csv=True,
			write_json=True,
			generate_plots=True,
		)
		result = SimulationResult(
			case_name="air_baseline",
			working_fluid="air",
			gas_solution=_make_gas_solution(),
			droplet_solution=_make_droplet_solution(),
			diagnostics=diagnostics,
			validation_report=validation,
			output_metadata=output_metadata,
		)

		self.assertEqual(result.case_name, "air_baseline")
		self.assertEqual(result.working_fluid, "air")
		self.assertEqual(result.diagnostics.status, "success")
		self.assertEqual(result.validation_report.status, "pass")
		self.assertIn("pressure", result.output_metadata.plot_paths)

	def test_result_model_preserves_structured_alignment(self) -> None:
		result = SimulationResult(
			case_name=None,
			working_fluid="steam",
			gas_solution=_make_gas_solution(),
			droplet_solution=_make_droplet_solution(),
			diagnostics=RunDiagnostics(status="warning"),
			validation_report=None,
			output_metadata=None,
		)

		self.assertEqual(result.gas_solution.x_values[0], result.droplet_solution.x_values[0])
		self.assertIsNone(result.validation_report)
		self.assertIsNone(result.output_metadata)


if __name__ == "__main__":
	unittest.main()