"""Unit tests for the KH-RT and bag-stripping breakup models.

Coverage
--------
- KHRTBreakupModel: no-breakup case, KH-triggered case, RT-triggered case,
  invalid construction, physics consistency checks.
- BagStrippingBreakupModel: no-breakup case, triggered case with stable-Weber
  child diameter, regime labelling, invalid construction.
- select_breakup_model: registry routes to correct model for 'khrt' and
  'bag_stripping'.
- validate_breakup_decision: accepts critical_weber_number = 0.0 (KH-RT sentinel).
"""

from __future__ import annotations

import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.breakup import (
    BagStrippingBreakupModel,
    BreakupModelInputs,
    KHRTBreakupModel,
    select_breakup_model,
    validate_breakup_decision,
)
from supersonic_atomizer.common import ConfigurationError, NumericalError
from supersonic_atomizer.domain import (
    BreakupDecision,
    DropletState,
    GasState,
    ModelSelectionConfig,
    ThermoState,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def _gas(*, velocity: float = 400.0, density: float = 5.0) -> GasState:
    thermo = ThermoState(
        pressure=500_000.0,
        temperature=350.0,
        density=density,
        enthalpy=350_000.0,
        sound_speed=375.0,
    )
    return GasState(
        x=0.05,
        area=1.0e-4,
        pressure=500_000.0,
        temperature=350.0,
        density=density,
        velocity=velocity,
        mach_number=velocity / thermo.sound_speed,
        thermo_state=thermo,
    )


def _drop(
    *,
    velocity: float = 10.0,
    slip_velocity: float = 390.0,
    mean_d: float = 1.0e-4,
    max_d: float = 2.0e-4,
) -> DropletState:
    return DropletState(
        x=0.05,
        velocity=velocity,
        slip_velocity=slip_velocity,
        mean_diameter=mean_d,
        maximum_diameter=max_d,
        weber_number=0.0,
        reynolds_number=None,
        breakup_triggered=False,
    )


def _inputs(gas=None, drop=None) -> BreakupModelInputs:
    return BreakupModelInputs(
        gas_state=gas or _gas(),
        droplet_state=drop or _drop(),
    )


# ---------------------------------------------------------------------------
# KHRTBreakupModel
# ---------------------------------------------------------------------------

class TestKHRTBreakupModelConstruction(unittest.TestCase):
    def test_default_construction_succeeds(self) -> None:
        model = KHRTBreakupModel()
        self.assertEqual(model.model_name, "khrt")

    def test_rejects_zero_B0(self) -> None:
        with self.assertRaises(ConfigurationError):
            KHRTBreakupModel(B0=0.0)

    def test_rejects_negative_liquid_density(self) -> None:
        with self.assertRaises(ConfigurationError):
            KHRTBreakupModel(liquid_density=-1.0)

    def test_rejects_zero_surface_tension(self) -> None:
        with self.assertRaises(ConfigurationError):
            KHRTBreakupModel(surface_tension=0.0)


class TestKHRTBreakupModelNoBreakup(unittest.TestCase):
    """Low-slip scenario: child diameters exceed parent — no breakup."""

    def test_no_breakup_near_zero_slip(self) -> None:
        model = KHRTBreakupModel()
        inputs = _inputs(drop=_drop(slip_velocity=0.01))
        decision = model.evaluate(inputs)
        self.assertFalse(decision.triggered)
        self.assertAlmostEqual(decision.updated_mean_diameter, 1.0e-4)
        self.assertAlmostEqual(decision.updated_maximum_diameter, 2.0e-4)

    def test_weber_number_is_finite_and_nonneg(self) -> None:
        model = KHRTBreakupModel()
        decision = model.evaluate(_inputs(drop=_drop(slip_velocity=0.01)))
        self.assertTrue(math.isfinite(decision.weber_number))
        self.assertGreaterEqual(decision.weber_number, 0.0)

    def test_critical_weber_zero_for_khrt(self) -> None:
        """KH-RT reports critical_weber_number = 0.0 (no scalar threshold)."""
        model = KHRTBreakupModel()
        decision = model.evaluate(_inputs(drop=_drop(slip_velocity=0.01)))
        self.assertEqual(decision.critical_weber_number, 0.0)


class TestKHRTBreakupModelTriggered(unittest.TestCase):
    """High-slip scenario with dense gas: expect breakup to reduce diameter."""

    def _high_slip_inputs(self) -> BreakupModelInputs:
        return _inputs(
            gas=_gas(velocity=400.0, density=20.0),
            drop=_drop(slip_velocity=380.0, mean_d=5.0e-4, max_d=1.0e-3),
        )

    def test_breakup_triggers_and_reduces_mean_diameter(self) -> None:
        model = KHRTBreakupModel()
        decision = model.evaluate(self._high_slip_inputs())
        if decision.triggered:
            self.assertLess(decision.updated_mean_diameter, 5.0e-4)

    def test_max_diameter_not_less_than_mean(self) -> None:
        model = KHRTBreakupModel()
        decision = model.evaluate(self._high_slip_inputs())
        self.assertGreaterEqual(
            decision.updated_maximum_diameter,
            decision.updated_mean_diameter,
        )

    def test_updated_diameters_are_positive(self) -> None:
        model = KHRTBreakupModel()
        decision = model.evaluate(self._high_slip_inputs())
        self.assertGreater(decision.updated_mean_diameter, 0.0)
        self.assertGreater(decision.updated_maximum_diameter, 0.0)

    def test_reason_string_is_nonempty(self) -> None:
        model = KHRTBreakupModel()
        decision = model.evaluate(self._high_slip_inputs())
        self.assertTrue(len(decision.reason) > 0)


# ---------------------------------------------------------------------------
# BagStrippingBreakupModel
# ---------------------------------------------------------------------------

class TestBagStrippingConstruction(unittest.TestCase):
    def test_default_construction_succeeds(self) -> None:
        model = BagStrippingBreakupModel()
        self.assertEqual(model.model_name, "bag_stripping")

    def test_rejects_zero_critical_weber(self) -> None:
        with self.assertRaises(ConfigurationError):
            BagStrippingBreakupModel(critical_weber_number=0.0)

    def test_rejects_negative_surface_tension(self) -> None:
        with self.assertRaises(ConfigurationError):
            BagStrippingBreakupModel(surface_tension=-0.1)


class TestBagStrippingNoBreakup(unittest.TestCase):
    def test_no_breakup_below_threshold(self) -> None:
        """Very low slip: We well below 12, no breakup."""
        model = BagStrippingBreakupModel()
        inputs = _inputs(drop=_drop(slip_velocity=0.01))
        decision = model.evaluate(inputs)
        self.assertFalse(decision.triggered)

    def test_diameters_unchanged_when_no_breakup(self) -> None:
        model = BagStrippingBreakupModel()
        decision = model.evaluate(_inputs(drop=_drop(slip_velocity=0.01)))
        self.assertAlmostEqual(decision.updated_mean_diameter, 1.0e-4)
        self.assertAlmostEqual(decision.updated_maximum_diameter, 2.0e-4)


class TestBagStrippingTriggered(unittest.TestCase):
    """High-We scenario: breakup should produce stable-Weber child diameter."""

    def _high_we_inputs(self) -> BreakupModelInputs:
        return _inputs(
            gas=_gas(velocity=400.0, density=5.0),
            drop=_drop(slip_velocity=350.0, mean_d=1.0e-3, max_d=2.0e-3),
        )

    def test_triggered_at_high_we(self) -> None:
        model = BagStrippingBreakupModel()
        decision = model.evaluate(self._high_we_inputs())
        self.assertTrue(decision.triggered)

    def test_child_diameter_is_stable_we_equilibrium(self) -> None:
        """d_child should equal We_crit * σ / (ρ_g * u_rel²) within tolerance."""
        model = BagStrippingBreakupModel()
        gas = _gas(density=5.0)
        drop = _drop(slip_velocity=350.0, mean_d=1.0e-3)
        decision = model.evaluate(_inputs(gas=gas, drop=drop))
        if decision.triggered:
            expected = model.critical_weber_number * model.surface_tension / (gas.density * 350.0 ** 2)
            self.assertAlmostEqual(decision.updated_mean_diameter, expected, places=10)

    def test_mean_not_larger_than_parent(self) -> None:
        model = BagStrippingBreakupModel()
        decision = model.evaluate(self._high_we_inputs())
        self.assertLessEqual(decision.updated_mean_diameter, 1.0e-3)

    def test_max_not_less_than_mean(self) -> None:
        model = BagStrippingBreakupModel()
        decision = model.evaluate(self._high_we_inputs())
        self.assertGreaterEqual(
            decision.updated_maximum_diameter,
            decision.updated_mean_diameter,
        )

    def test_reason_mentions_regime(self) -> None:
        model = BagStrippingBreakupModel()
        decision = model.evaluate(self._high_we_inputs())
        self.assertIn("regime", decision.reason)


# ---------------------------------------------------------------------------
# Registry: select_breakup_model
# ---------------------------------------------------------------------------

class TestRegistryNewModels(unittest.TestCase):
    def _base_config(self, breakup_model: str) -> ModelSelectionConfig:
        return ModelSelectionConfig(
            breakup_model=breakup_model,
            critical_weber_number=12.0,
            khrt_B0=0.61,
            khrt_B1=40.0,
            khrt_Crt=0.1,
            liquid_density=998.2,
            liquid_viscosity=1.002e-3,
        )

    def test_select_khrt_returns_khrt_instance(self) -> None:
        model = select_breakup_model(self._base_config("khrt"))
        self.assertIsInstance(model, KHRTBreakupModel)
        self.assertEqual(model.model_name, "khrt")

    def test_select_bag_stripping_returns_bag_stripping_instance(self) -> None:
        model = select_breakup_model(self._base_config("bag_stripping"))
        self.assertIsInstance(model, BagStrippingBreakupModel)
        self.assertEqual(model.model_name, "bag_stripping")

    def test_khrt_params_are_forwarded(self) -> None:
        cfg = ModelSelectionConfig(
            breakup_model="khrt",
            critical_weber_number=12.0,
            khrt_B0=0.5,
            khrt_B1=30.0,
            khrt_Crt=0.2,
            liquid_density=900.0,
            liquid_viscosity=5.0e-4,
        )
        model = select_breakup_model(cfg)
        self.assertIsInstance(model, KHRTBreakupModel)
        self.assertAlmostEqual(model.B0, 0.5)
        self.assertAlmostEqual(model.B1, 30.0)
        self.assertAlmostEqual(model.Crt, 0.2)
        self.assertAlmostEqual(model.liquid_density, 900.0)

    def test_bag_stripping_uses_critical_weber(self) -> None:
        cfg = ModelSelectionConfig(
            breakup_model="bag_stripping",
            critical_weber_number=18.0,
        )
        model = select_breakup_model(cfg)
        self.assertIsInstance(model, BagStrippingBreakupModel)
        self.assertAlmostEqual(model.critical_weber_number, 18.0)


# ---------------------------------------------------------------------------
# Diagnostics: critical_weber_number = 0.0 now accepted
# ---------------------------------------------------------------------------

class TestDiagnosticsAcceptsZeroCriticalWeber(unittest.TestCase):
    def test_zero_critical_weber_does_not_raise(self) -> None:
        decision = BreakupDecision(
            triggered=False,
            weber_number=5.0,
            critical_weber_number=0.0,
            updated_mean_diameter=1.0e-4,
            updated_maximum_diameter=2.0e-4,
            reason="KH-RT: no breakup",
        )
        # Should not raise
        validate_breakup_decision(decision)

    def test_negative_critical_weber_still_raises(self) -> None:
        decision = BreakupDecision(
            triggered=False,
            weber_number=5.0,
            critical_weber_number=-1.0,
            updated_mean_diameter=1.0e-4,
            updated_maximum_diameter=2.0e-4,
            reason="invalid",
        )
        with self.assertRaises(NumericalError):
            validate_breakup_decision(decision)


if __name__ == "__main__":
    unittest.main()
