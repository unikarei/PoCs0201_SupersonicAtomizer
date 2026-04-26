from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.domain import (
	BreakupDecision,
	CouplingSourceTerms,
	DropletSolution,
	DropletState,
	GasSolution,
	GasState,
	ThermoState,
)


class TestRuntimeSolverStateModels(unittest.TestCase):
	def test_constructs_runtime_solver_state_models(self) -> None:
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
		gas_solution = GasSolution(
			states=(gas_state,),
			x_values=(0.0,),
			area_values=(1.0e-4,),
			pressure_values=(100000.0,),
			temperature_values=(500.0,),
			density_values=(0.7,),
			velocity_values=(250.0,),
			mach_number_values=(0.6,),
		)
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
		droplet_solution = DropletSolution(
			states=(droplet_state,),
			x_values=(0.0,),
			velocity_values=(10.0,),
			slip_velocity_values=(240.0,),
			mean_diameter_values=(1.0e-4,),
			maximum_diameter_values=(3.0e-4,),
			weber_number_values=(12.0,),
			reynolds_number_values=(250.0,),
			breakup_flags=(False,),
			smd_diameter_values=(1.1e-4,),
			diameter_stddev_values=(1.0e-5,),
			coupling_source_terms=CouplingSourceTerms(
				mass_source_values=(0.0,),
				momentum_source_values=(0.0,),
				energy_source_values=(0.0,),
			),
		)
		breakup_decision = BreakupDecision(
			triggered=True,
			weber_number=15.0,
			critical_weber_number=12.0,
			updated_mean_diameter=7.0e-5,
			updated_maximum_diameter=2.0e-4,
			reason="threshold_exceeded",
		)

		self.assertEqual(gas_state.thermo_state.sound_speed, 420.0)
		self.assertEqual(gas_solution.velocity_values[0], 250.0)
		self.assertEqual(droplet_solution.breakup_flags[0], False)
		self.assertEqual(droplet_solution.smd_diameter_values[0], 1.1e-4)
		self.assertTrue(breakup_decision.triggered)

	def test_gas_solution_rejects_mismatched_array_lengths(self) -> None:
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

		with self.assertRaises(ValueError):
			GasSolution(
				states=(gas_state,),
				x_values=(0.0, 0.1),
				area_values=(1.0e-4,),
				pressure_values=(100000.0,),
				temperature_values=(500.0,),
				density_values=(0.7,),
				velocity_values=(250.0,),
				mach_number_values=(0.6,),
			)

	def test_droplet_solution_rejects_mismatched_array_lengths(self) -> None:
		droplet_state = DropletState(
			x=0.0,
			velocity=10.0,
			slip_velocity=240.0,
			mean_diameter=1.0e-4,
			maximum_diameter=3.0e-4,
			weber_number=12.0,
		)

		with self.assertRaises(ValueError):
			DropletSolution(
				states=(droplet_state,),
				x_values=(0.0,),
				velocity_values=(10.0,),
				slip_velocity_values=(240.0,),
				mean_diameter_values=(1.0e-4,),
				maximum_diameter_values=(3.0e-4,),
				weber_number_values=(12.0, 13.0),
				reynolds_number_values=(None,),
				breakup_flags=(False,),
			)

	def test_droplet_solution_rejects_misaligned_optional_moment_lengths(self) -> None:
		droplet_state = DropletState(
			x=0.0,
			velocity=10.0,
			slip_velocity=240.0,
			mean_diameter=1.0e-4,
			maximum_diameter=3.0e-4,
			weber_number=12.0,
		)

		with self.assertRaises(ValueError):
			DropletSolution(
				states=(droplet_state,),
				x_values=(0.0,),
				velocity_values=(10.0,),
				slip_velocity_values=(240.0,),
				mean_diameter_values=(1.0e-4,),
				maximum_diameter_values=(3.0e-4,),
				weber_number_values=(12.0,),
				reynolds_number_values=(None,),
				breakup_flags=(False,),
				smd_diameter_values=(1.0e-4, 1.1e-4),
			)


if __name__ == "__main__":
	unittest.main()