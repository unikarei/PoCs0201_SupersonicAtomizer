from supersonic_atomizer.breakup.tab import TABBreakupModel
from supersonic_atomizer.breakup.interfaces import BreakupModelInputs
from supersonic_atomizer.domain.state_models import DropletState, GasState


def make_gas_state(x=0.0):
    # Minimal placeholder GasState required by interface; only x used here.
    from supersonic_atomizer.domain.state_models import GasState, ThermoState

    thermo = ThermoState(pressure=101325.0, temperature=300.0, density=1.2, enthalpy=0.0, sound_speed=340.0)
    return GasState(x=x, area=1.0, pressure=101325.0, temperature=300.0, density=1.2, velocity=10.0, mach_number=0.03, thermo_state=thermo)


def test_tab_triggers_on_high_weber():
    # Choose parameters that make the oscillator easily triggered
    model = TABBreakupModel(spring_k=1e-6, damping_c=1e-8, breakup_threshold=0.1, reduction_fraction=0.5)
    gs = make_gas_state()
    ds = DropletState(x=0.0, velocity=0.0, slip_velocity=10.0, mean_diameter=50e-6, maximum_diameter=80e-6, weber_number=20.0)
    inputs = BreakupModelInputs(gas_state=gs, droplet_state=ds, dt=1e-2)
    decision = model.evaluate(inputs)
    assert decision.triggered is True
    assert decision.updated_mean_diameter < ds.mean_diameter


def test_tab_no_trigger_below_threshold():
    model = TABBreakupModel(spring_k=1e-3, damping_c=1e-6, breakup_threshold=10.0, reduction_fraction=0.5)
    gs = make_gas_state()
    ds = DropletState(x=0.0, velocity=0.0, slip_velocity=1.0, mean_diameter=100e-6, maximum_diameter=120e-6, weber_number=6.0)
    inputs = BreakupModelInputs(gas_state=gs, droplet_state=ds, dt=1e-3)
    decision = model.evaluate(inputs)
    assert decision.triggered is False
    assert decision.updated_mean_diameter == ds.mean_diameter
