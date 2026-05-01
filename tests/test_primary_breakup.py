import math

from supersonic_atomizer.solvers.droplet.primary_breakup import estimate_primary_breakup
from supersonic_atomizer.domain import DropletInjectionConfig
from supersonic_atomizer.domain import BoundaryConditionConfig, GeometryConfig, FluidConfig
from supersonic_atomizer.geometry.geometry_model import build_geometry_model
from supersonic_atomizer.config.translator import translate_case_config
import yaml


def test_primary_breakup_basic():
    # construct a fake gas state via a minimal case YAML and use inlet gas state
    case_yaml = {
        'fluid': {'working_fluid': 'air'},
        'boundary_conditions': {'Pt_in': 300000, 'Tt_in': 300, 'Ps_out': 25000},
        'geometry': {'x_start': 0, 'x_end': 0.5, 'n_cells': 10, 'area_distribution': {'type': 'table', 'x': [0, 0.5], 'A': [0.01, 0.01]}},
        # include required droplet fields for translator even though injection_mode is liquid_jet_injection
        'droplet_injection': {
            'injection_mode': 'liquid_jet_injection',
            'droplet_velocity_in': 0.0,
            'droplet_diameter_mean_in': 1e-4,
            'droplet_diameter_max_in': 2e-4,
            'liquid_jet_diameter': 0.001,
            'liquid_velocity': 10.0,
            'liquid_density': 998.2,
            'liquid_viscosity': 0.001,
            'surface_tension': 0.072,
            'water_mass_flow_rate': 0.01,
        }
    }
    # translate minimal config and build geometry model to get a gas_state-like object
    case = translate_case_config(case_yaml)
    geom_model = build_geometry_model(case.geometry)
    # create a minimal GasState-like object using geometry first node and some estimated gas values
    from supersonic_atomizer.domain.state_models import GasState, ThermoState

    thermo = ThermoState(pressure=300000, temperature=300, density=1.2, enthalpy=0.0, sound_speed=343.0, dynamic_viscosity=1.8e-5)
    gas_state = GasState(x=0.0, area=geom_model.area_at(0.0), pressure=300000, temperature=300, density=1.2, velocity=100.0, mach_number=0.3, thermo_state=thermo)

    result = estimate_primary_breakup(
        liquid_diameter=case.droplet_injection.liquid_jet_diameter,
        liquid_velocity=case.droplet_injection.liquid_velocity,
        gas_state=gas_state,
        surface_tension=case.droplet_injection.surface_tension,
        liquid_density=case.droplet_injection.liquid_density,
        primary_coeff=5.0,
    )

    assert result.L_primary_breakup > 0.0
    assert result.generated_mean_diameter > 0.0
    assert result.generated_maximum_diameter >= result.generated_mean_diameter
