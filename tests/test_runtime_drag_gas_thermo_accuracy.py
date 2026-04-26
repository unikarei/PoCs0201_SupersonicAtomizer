from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.common import ModelSelectionError, ThermoError
from supersonic_atomizer.config.defaults import apply_config_defaults
from supersonic_atomizer.config.semantics import validate_semantic_config
from supersonic_atomizer.domain import (
    BoundaryConditionConfig,
    CaseConfig,
    DropletInjectionConfig,
    FluidConfig,
    GeometryConfig,
    ModelSelectionConfig,
    OutputConfig,
    ThermoState,
    GasState,
)
from supersonic_atomizer.geometry import build_geometry_model
from supersonic_atomizer.solvers.droplet import (
    NonSphericalSphereDragModel,
    StandardSphereDragInputs,
    StandardSphereDragModel,
    initialize_droplet_state,
    select_drag_model,
)
from supersonic_atomizer.solvers.gas import solve_quasi_1d_gas_flow
from supersonic_atomizer.thermo import IF97SteamThermoProvider, select_thermo_provider


class TestPhase30SemanticValidation(unittest.TestCase):
    def _valid_config(self) -> dict:
        return apply_config_defaults(
            {
                "fluid": {"working_fluid": "steam"},
                "boundary_conditions": {
                    "Pt_in": 600000.0,
                    "Tt_in": 500.0,
                    "Ps_out": 100000.0,
                },
                "geometry": {
                    "x_start": 0.0,
                    "x_end": 0.1,
                    "n_cells": 10,
                    "area_distribution": {
                        "type": "table",
                        "x": [0.0, 0.1],
                        "A": [1.0e-4, 1.2e-4],
                    },
                },
                "droplet_injection": {
                    "droplet_velocity_in": 10.0,
                    "droplet_diameter_mean_in": 1.0e-4,
                    "droplet_diameter_max_in": 2.0e-4,
                },
            }
        )

    def test_accepts_new_phase30_model_fields(self) -> None:
        raw_config = self._valid_config()
        raw_config["models"]["drag_model"] = "nonspherical_sphere"
        raw_config["models"]["droplet_sphericity"] = 0.82
        raw_config["models"]["droplet_density"] = 950.0
        raw_config["models"]["gas_solver_mode"] = "shock_refined"
        raw_config["models"]["steam_property_model"] = "if97"

        validated = validate_semantic_config(raw_config)

        self.assertIs(validated, raw_config)

    def test_rejects_invalid_droplet_sphericity(self) -> None:
        raw_config = self._valid_config()
        raw_config["models"]["droplet_sphericity"] = 1.2

        with self.assertRaises(ValueError):
            validate_semantic_config(raw_config)

    def test_rejects_invalid_gas_solver_mode(self) -> None:
        raw_config = self._valid_config()
        raw_config["models"]["gas_solver_mode"] = "roe"

        with self.assertRaises(ValueError):
            validate_semantic_config(raw_config)


class TestPhase30DragModels(unittest.TestCase):
    def test_standard_sphere_uses_high_re_asymptote(self) -> None:
        evaluation = StandardSphereDragModel().evaluate(
            StandardSphereDragInputs(
                gas_density=50.0,
                slip_velocity=500.0,
                droplet_diameter=2.0e-3,
                dynamic_viscosity=1.0e-5,
            )
        )

        self.assertGreater(evaluation.reynolds_number, 1000.0)
        self.assertAlmostEqual(evaluation.drag_coefficient, 0.44, places=8)

    def test_nonspherical_drag_exceeds_standard_for_same_inputs(self) -> None:
        inputs = StandardSphereDragInputs(
            gas_density=1.2,
            slip_velocity=25.0,
            droplet_diameter=1.0e-4,
            dynamic_viscosity=1.8e-5,
        )
        standard = StandardSphereDragModel().evaluate(inputs)
        nonspherical = NonSphericalSphereDragModel(sphericity=0.7).evaluate(inputs)

        self.assertGreater(nonspherical.drag_coefficient, standard.drag_coefficient)
        self.assertGreater(nonspherical.acceleration, standard.acceleration)

    def test_select_drag_model_resolves_nonspherical_model(self) -> None:
        model = select_drag_model(
            ModelSelectionConfig(
                drag_model="nonspherical_sphere",
                droplet_density=970.0,
                droplet_sphericity=0.75,
            )
        )

        self.assertIsInstance(model, NonSphericalSphereDragModel)
        self.assertAlmostEqual(model.droplet_density, 970.0)
        self.assertAlmostEqual(model.sphericity, 0.75)

    def test_select_drag_model_rejects_unknown_name(self) -> None:
        with self.assertRaises(ModelSelectionError):
            select_drag_model(ModelSelectionConfig(drag_model="unknown_drag"))

    def test_dynamic_viscosity_affects_reynolds_number_in_droplet_initialization(self) -> None:
        gas_state_low_mu = GasState(
            x=0.0,
            area=1.0e-4,
            pressure=100000.0,
            temperature=400.0,
            density=1.2,
            velocity=50.0,
            mach_number=0.2,
            thermo_state=ThermoState(
                pressure=100000.0,
                temperature=400.0,
                density=1.2,
                enthalpy=1.0,
                sound_speed=300.0,
                dynamic_viscosity=1.0e-5,
            ),
        )
        gas_state_high_mu = GasState(
            x=0.0,
            area=1.0e-4,
            pressure=100000.0,
            temperature=400.0,
            density=1.2,
            velocity=50.0,
            mach_number=0.2,
            thermo_state=ThermoState(
                pressure=100000.0,
                temperature=400.0,
                density=1.2,
                enthalpy=1.0,
                sound_speed=300.0,
                dynamic_viscosity=5.0e-5,
            ),
        )
        injection = DropletInjectionConfig(
            droplet_velocity_in=10.0,
            droplet_diameter_mean_in=1.0e-4,
            droplet_diameter_max_in=2.0e-4,
        )

        low_mu_state = initialize_droplet_state(
            gas_state=gas_state_low_mu,
            injection_config=injection,
            drag_model=StandardSphereDragModel(),
        )
        high_mu_state = initialize_droplet_state(
            gas_state=gas_state_high_mu,
            injection_config=injection,
            drag_model=StandardSphereDragModel(),
        )

        self.assertGreater(low_mu_state.reynolds_number, high_mu_state.reynolds_number)


class TestPhase30ShockRefinedGasSolver(unittest.TestCase):
    def _build_laval_geometry(self):
        return build_geometry_model(
            GeometryConfig(
                x_start=0.0,
                x_end=0.2,
                n_cells=20,
                area_definition={
                    "type": "table",
                    "x": [0.0, 0.05, 0.1, 0.15, 0.2],
                    "A": [1.8e-4, 1.3e-4, 1.0e-4, 1.2e-4, 1.4e-4],
                },
            )
        )

    def test_shock_refined_mode_adds_local_samples(self) -> None:
        geometry_model = self._build_laval_geometry()
        baseline = solve_quasi_1d_gas_flow(
            geometry_model=geometry_model,
            boundary_conditions=BoundaryConditionConfig(
                Pt_in=300000.0,
                Tt_in=320.0,
                Ps_out=200000.0,
            ),
            thermo_provider=select_thermo_provider(
                CaseConfig(
                    fluid=FluidConfig(working_fluid="air"),
                    boundary_conditions=BoundaryConditionConfig(Pt_in=300000.0, Tt_in=320.0, Ps_out=200000.0),
                    geometry=GeometryConfig(
                        x_start=0.0,
                        x_end=0.2,
                        n_cells=20,
                        area_definition={
                            "type": "table",
                            "x": [0.0, 0.05, 0.1, 0.15, 0.2],
                            "A": [1.8e-4, 1.3e-4, 1.0e-4, 1.2e-4, 1.4e-4],
                        },
                    ),
                    droplet_injection=DropletInjectionConfig(
                        droplet_velocity_in=10.0,
                        droplet_diameter_mean_in=1.0e-4,
                        droplet_diameter_max_in=2.0e-4,
                    ),
                    models=ModelSelectionConfig(),
                    outputs=OutputConfig(),
                )
            ),
        )
        refined = solve_quasi_1d_gas_flow(
            geometry_model=geometry_model,
            boundary_conditions=BoundaryConditionConfig(
                Pt_in=300000.0,
                Tt_in=320.0,
                Ps_out=200000.0,
            ),
            thermo_provider=select_thermo_provider(
                CaseConfig(
                    fluid=FluidConfig(working_fluid="air"),
                    boundary_conditions=BoundaryConditionConfig(Pt_in=300000.0, Tt_in=320.0, Ps_out=200000.0),
                    geometry=GeometryConfig(
                        x_start=0.0,
                        x_end=0.2,
                        n_cells=20,
                        area_definition={
                            "type": "table",
                            "x": [0.0, 0.05, 0.1, 0.15, 0.2],
                            "A": [1.8e-4, 1.3e-4, 1.0e-4, 1.2e-4, 1.4e-4],
                        },
                    ),
                    droplet_injection=DropletInjectionConfig(
                        droplet_velocity_in=10.0,
                        droplet_diameter_mean_in=1.0e-4,
                        droplet_diameter_max_in=2.0e-4,
                    ),
                    models=ModelSelectionConfig(gas_solver_mode="shock_refined"),
                    outputs=OutputConfig(),
                )
            ),
            gas_solver_mode="shock_refined",
        )

        self.assertGreater(len(refined.states), len(baseline.states))
        self.assertTrue(any("gas_solver_mode=shock_refined" in m for m in refined.diagnostics.messages))
        self.assertTrue(any("refined_sample_count=" in m for m in refined.diagnostics.messages))


class TestPhase30IF97SteamProvider(unittest.TestCase):
    def test_select_thermo_provider_returns_if97_provider(self) -> None:
        case_config = CaseConfig(
            fluid=FluidConfig(working_fluid="steam"),
            boundary_conditions=BoundaryConditionConfig(Pt_in=500000.0, Tt_in=500.0, Ps_out=100000.0),
            geometry=GeometryConfig(
                x_start=0.0,
                x_end=0.1,
                n_cells=10,
                area_definition={"type": "table", "x": [0.0, 0.1], "A": [1.0e-4, 1.1e-4]},
            ),
            droplet_injection=DropletInjectionConfig(
                droplet_velocity_in=10.0,
                droplet_diameter_mean_in=1.0e-4,
                droplet_diameter_max_in=2.0e-4,
            ),
            models=ModelSelectionConfig(steam_property_model="if97"),
            outputs=OutputConfig(),
        )

        provider = select_thermo_provider(case_config)

        self.assertIsInstance(provider, IF97SteamThermoProvider)

    def test_if97_provider_evaluates_vapor_region_state(self) -> None:
        provider = IF97SteamThermoProvider()

        state = provider.evaluate_state(pressure=200000.0, temperature=450.0)

        self.assertGreater(state.density, 0.0)
        self.assertGreater(state.enthalpy, 0.0)
        self.assertGreater(state.sound_speed, 0.0)
        self.assertGreater(state.dynamic_viscosity, 0.0)

    def test_if97_provider_rejects_non_vapor_region_state(self) -> None:
        provider = IF97SteamThermoProvider()

        with self.assertRaises(ThermoError):
            provider.evaluate_state(pressure=3_000_000.0, temperature=350.0)


if __name__ == "__main__":
    unittest.main()
