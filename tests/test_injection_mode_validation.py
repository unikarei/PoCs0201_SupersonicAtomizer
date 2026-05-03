"""P9-T06 — Unit tests for injection_mode schema validation, semantic validation,
and config translation.

Covers:
- schema.py: injection_mode accepted as optional string; liquid-jet numeric fields
  accepted when present
- semantics.py: invalid injection_mode value rejected; liquid_jet required fields
  enforced when mode is liquid_jet_injection; droplet_injection fields validated
  when mode is droplet_injection
- translator.py: injection_mode and liquid-jet fields appear in DropletInjectionConfig
"""

from __future__ import annotations

import pytest

from supersonic_atomizer.config.schema import validate_raw_config_schema
from supersonic_atomizer.config.semantics import validate_semantic_config
from supersonic_atomizer.config.translator import translate_case_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_raw_config(**droplet_overrides) -> dict:
    """Minimal valid YAML-equivalent dict for droplet_injection mode."""
    config = {
        "fluid": {"working_fluid": "air"},
        "boundary_conditions": {"Pt_in": 300_000, "Tt_in": 300.0, "Ps_out": 25_000},
        "geometry": {
            "x_start": 0.0,
            "x_end": 0.5,
            "n_cells": 20,
            "area_distribution": {
                "type": "table",
                "x": [0.0, 0.5],
                "A": [0.01, 0.01],
            },
        },
        "droplet_injection": {
            "droplet_velocity_in": 5.0,
            "droplet_diameter_mean_in": 50e-6,
            "droplet_diameter_max_in": 100e-6,
        },
    }
    config["droplet_injection"].update(droplet_overrides)
    return config


def _liquid_jet_fields() -> dict:
    return {
        "injection_mode": "liquid_jet_injection",
        "liquid_jet_diameter": 0.001,
        "liquid_mass_flow_rate": 0.01,
        "liquid_velocity": 10.0,
        "liquid_density": 998.2,
        "liquid_viscosity": 0.001,
        "surface_tension": 0.072,
    }


# ---------------------------------------------------------------------------
# Schema validation — injection_mode field
# ---------------------------------------------------------------------------

class TestSchemaInjectionMode:
    def test_default_droplet_mode_passes_schema(self):
        """No injection_mode supplied → schema passes."""
        raw = _base_raw_config()
        validate_raw_config_schema(raw)  # must not raise

    def test_explicit_droplet_injection_passes_schema(self):
        raw = _base_raw_config(injection_mode="droplet_injection")
        validate_raw_config_schema(raw)

    def test_liquid_jet_injection_passes_schema(self):
        raw = _base_raw_config(**_liquid_jet_fields())
        validate_raw_config_schema(raw)

    def test_liquid_jet_injection_without_droplet_fields_passes_schema(self):
        raw = _base_raw_config(**_liquid_jet_fields())
        raw["droplet_injection"].pop("droplet_velocity_in")
        raw["droplet_injection"].pop("droplet_diameter_mean_in")
        raw["droplet_injection"].pop("droplet_diameter_max_in")
        validate_raw_config_schema(raw)

    def test_injection_mode_non_string_rejected_by_schema(self):
        raw = _base_raw_config(injection_mode=42)
        with pytest.raises(ValueError, match="injection_mode"):
            validate_raw_config_schema(raw)

    def test_liquid_jet_diameter_non_numeric_rejected(self):
        raw = _base_raw_config(**{**_liquid_jet_fields(), "liquid_jet_diameter": "big"})
        with pytest.raises(ValueError, match="liquid_jet_diameter"):
            validate_raw_config_schema(raw)


# ---------------------------------------------------------------------------
# Semantic validation — injection_mode
# ---------------------------------------------------------------------------

class TestSemanticsInjectionMode:
    def test_unknown_injection_mode_rejected(self):
        raw = _base_raw_config(injection_mode="unknown_mode")
        with pytest.raises(ValueError, match="injection_mode"):
            validate_semantic_config(raw)

    def test_liquid_jet_missing_required_field_rejected(self):
        """liquid_jet_injection without surface_tension must fail."""
        fields = _liquid_jet_fields()
        del fields["surface_tension"]
        raw = _base_raw_config(**fields)
        with pytest.raises(ValueError, match="surface_tension"):
            validate_semantic_config(raw)

    def test_liquid_jet_negative_diameter_rejected(self):
        raw = _base_raw_config(**{**_liquid_jet_fields(), "liquid_jet_diameter": -0.001})
        with pytest.raises(ValueError, match="liquid_jet_diameter"):
            validate_semantic_config(raw)

    def test_liquid_jet_zero_surface_tension_rejected(self):
        raw = _base_raw_config(**{**_liquid_jet_fields(), "surface_tension": 0.0})
        with pytest.raises(ValueError, match="surface_tension"):
            validate_semantic_config(raw)

    def test_valid_liquid_jet_passes_semantics(self):
        raw = _base_raw_config(**_liquid_jet_fields())
        validate_semantic_config(raw)  # must not raise

    def test_liquid_jet_without_droplet_fields_passes_semantics(self):
        raw = _base_raw_config(**_liquid_jet_fields())
        raw["droplet_injection"].pop("droplet_velocity_in")
        raw["droplet_injection"].pop("droplet_diameter_mean_in")
        raw["droplet_injection"].pop("droplet_diameter_max_in")
        validate_semantic_config(raw)

    def test_valid_droplet_injection_passes_semantics(self):
        raw = _base_raw_config(injection_mode="droplet_injection")
        validate_semantic_config(raw)  # must not raise

    def test_default_droplet_injection_passes_semantics(self):
        raw = _base_raw_config()
        validate_semantic_config(raw)


# ---------------------------------------------------------------------------
# Translation — injection_mode and liquid-jet fields in DropletInjectionConfig
# ---------------------------------------------------------------------------

class TestTranslatorInjectionMode:
    def test_default_injection_mode_is_droplet_injection(self):
        raw = _base_raw_config()
        case = translate_case_config(raw)
        assert case.droplet_injection.injection_mode == "droplet_injection"

    def test_explicit_droplet_injection_preserved(self):
        raw = _base_raw_config(injection_mode="droplet_injection")
        case = translate_case_config(raw)
        assert case.droplet_injection.injection_mode == "droplet_injection"

    def test_liquid_jet_injection_mode_preserved(self):
        raw = _base_raw_config(**_liquid_jet_fields())
        case = translate_case_config(raw)
        assert case.droplet_injection.injection_mode == "liquid_jet_injection"

    def test_liquid_jet_fields_translated(self):
        raw = _base_raw_config(**_liquid_jet_fields())
        case = translate_case_config(raw)
        di = case.droplet_injection
        assert di.liquid_jet_diameter == pytest.approx(0.001)
        assert di.liquid_mass_flow_rate == pytest.approx(0.01)
        assert di.liquid_velocity == pytest.approx(10.0)
        assert di.liquid_density == pytest.approx(998.2)
        assert di.liquid_viscosity == pytest.approx(0.001)
        assert di.surface_tension == pytest.approx(0.072)

    def test_liquid_jet_fields_absent_when_not_supplied(self):
        raw = _base_raw_config()
        case = translate_case_config(raw)
        di = case.droplet_injection
        assert di.liquid_jet_diameter is None
        assert di.liquid_velocity is None
        assert di.surface_tension is None

    def test_liquid_jet_droplet_fields_may_be_absent(self):
        raw = _base_raw_config(**_liquid_jet_fields())
        raw["droplet_injection"].pop("droplet_velocity_in")
        raw["droplet_injection"].pop("droplet_diameter_mean_in")
        raw["droplet_injection"].pop("droplet_diameter_max_in")
        case = translate_case_config(raw)
        di = case.droplet_injection
        assert di.droplet_velocity_in is None
        assert di.droplet_diameter_mean_in is None
        assert di.droplet_diameter_max_in is None
