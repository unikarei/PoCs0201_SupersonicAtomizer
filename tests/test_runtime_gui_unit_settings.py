"""Tests for Phase 24 unit settings — P24-T07.

Covers:
- UnitSpec dataclass
- UNIT_GROUPS / DEFAULT_UNITS consistency
- get_unit_spec
- convert_value / convert_series
- display_unit_label / field_display_label
- FIELD_UNIT_GROUP completeness
- GUIState unit fields and unit_preferences()
- unit_settings_page pure helpers
- extract_plot_series with unit_preferences
- result_to_table_rows with unit_preferences

All tests exercise pure-Python helpers only.
No live Streamlit session or browser is required.
"""

from __future__ import annotations

import pytest

from supersonic_atomizer.domain import (
    DropletSolution,
    DropletState,
    GasSolution,
    GasState,
    RunDiagnostics,
    SimulationResult,
    ThermoState,
)
from supersonic_atomizer.gui.pages.post_graphs import extract_plot_series
from supersonic_atomizer.gui.pages.post_table import generate_csv_content, result_to_table_rows
from supersonic_atomizer.gui.pages.unit_settings_page import (
    apply_unit_preference,
    get_unit_choices,
    get_unit_preference,
)
from supersonic_atomizer.gui.state import GUIState
from supersonic_atomizer.gui.unit_settings import (
    DEFAULT_UNITS,
    FIELD_UNIT_GROUP,
    UNIT_GROUPS,
    UnitSpec,
    convert_series,
    convert_value,
    display_unit_label,
    field_display_label,
    get_unit_spec,
)


# ── Shared fixture ────────────────────────────────────────────────────────────


@pytest.fixture()
def sample_result() -> SimulationResult:
    """Minimal two-point SimulationResult for unit-conversion tests.

    Gas: pressure (100 000 Pa, 95 000 Pa), temperature (300 K, 295 K)
    Droplets: mean_diameter (5e-5 m, 4e-5 m), x (0.0 m, 0.1 m)
    """
    thermo = ThermoState(
        pressure=100_000.0, temperature=300.0, density=1.2, enthalpy=1.0, sound_speed=340.0
    )
    gas_states = (
        GasState(0.0, 1.0e-4, 100_000.0, 300.0, 1.2, 50.0, 0.2, thermo),
        GasState(0.1, 8.0e-5, 95_000.0, 295.0, 1.15, 80.0, 0.3, thermo),
    )
    gas = GasSolution(
        states=gas_states,
        x_values=(0.0, 0.1),
        area_values=(1.0e-4, 8.0e-5),
        pressure_values=(100_000.0, 95_000.0),
        temperature_values=(300.0, 295.0),
        density_values=(1.2, 1.15),
        velocity_values=(50.0, 80.0),
        mach_number_values=(0.2, 0.3),
    )
    droplet_states = (
        DropletState(0.0, 10.0, 40.0, 5.0e-5, 1.0e-4, 2.0, 100.0, False),
        DropletState(0.1, 20.0, 60.0, 4.0e-5, 8.0e-5, 15.0, 150.0, True),
    )
    droplet = DropletSolution(
        states=droplet_states,
        x_values=(0.0, 0.1),
        velocity_values=(10.0, 20.0),
        slip_velocity_values=(40.0, 60.0),
        mean_diameter_values=(5.0e-5, 4.0e-5),
        maximum_diameter_values=(1.0e-4, 8.0e-5),
        weber_number_values=(2.0, 15.0),
        reynolds_number_values=(100.0, 150.0),
        breakup_flags=(False, True),
    )
    return SimulationResult(
        case_name="unit_test_case",
        working_fluid="air",
        gas_solution=gas,
        droplet_solution=droplet,
        diagnostics=RunDiagnostics(status="completed"),
    )


@pytest.fixture()
def full_prefs() -> dict[str, str]:
    """Full unit-preferences dict matching spec B.11 defaults."""
    return {
        "pressure":    "kPa",
        "temperature": "K",
        "velocity":    "m/s",
        "diameter":    "μm",
        "length":      "m",
        "area":        "m²",
        "density":     "kg/m³",
    }


# ── UnitSpec ──────────────────────────────────────────────────────────────────


class TestUnitSpec:
    def test_construction_with_default_offset(self) -> None:
        spec = UnitSpec("kPa", 1e-3)
        assert spec.label == "kPa"
        assert spec.scale == pytest.approx(1e-3)
        assert spec.offset == 0.0

    def test_construction_with_explicit_offset(self) -> None:
        spec = UnitSpec("°C", 1.0, -273.15)
        assert spec.offset == pytest.approx(-273.15)

    def test_immutable_label(self) -> None:
        spec = UnitSpec("kPa", 1e-3)
        with pytest.raises((AttributeError, TypeError)):
            spec.label = "Pa"  # type: ignore[misc]

    def test_immutable_scale(self) -> None:
        spec = UnitSpec("kPa", 1e-3)
        with pytest.raises((AttributeError, TypeError)):
            spec.scale = 1.0  # type: ignore[misc]


# ── UNIT_GROUPS / DEFAULT_UNITS consistency ───────────────────────────────────


class TestUnitGroupsConsistency:
    def test_all_expected_groups_present(self) -> None:
        for group in ("pressure", "temperature", "velocity", "diameter", "length", "area", "density"):
            assert group in UNIT_GROUPS, f"Group {group!r} missing from UNIT_GROUPS"

    def test_all_default_units_exist_in_their_groups(self) -> None:
        for group, unit_label in DEFAULT_UNITS.items():
            assert group in UNIT_GROUPS, f"DEFAULT_UNITS group {group!r} missing from UNIT_GROUPS"
            assert unit_label in UNIT_GROUPS[group], (
                f"Default {unit_label!r} not found in UNIT_GROUPS[{group!r}]"
            )

    def test_default_pressure_is_kpa(self) -> None:
        assert DEFAULT_UNITS["pressure"] == "kPa"

    def test_default_diameter_is_um(self) -> None:
        assert DEFAULT_UNITS["diameter"] == "μm"

    def test_default_temperature_is_k(self) -> None:
        assert DEFAULT_UNITS["temperature"] == "K"

    def test_default_velocity_is_ms(self) -> None:
        assert DEFAULT_UNITS["velocity"] == "m/s"

    def test_pressure_group_contains_expected_units(self) -> None:
        for unit in ("Pa", "kPa", "MPa", "bar"):
            assert unit in UNIT_GROUPS["pressure"]

    def test_diameter_group_contains_expected_units(self) -> None:
        for unit in ("m", "mm", "μm", "nm"):
            assert unit in UNIT_GROUPS["diameter"]

    def test_temperature_group_contains_celsius(self) -> None:
        assert "°C" in UNIT_GROUPS["temperature"]


# ── get_unit_spec ─────────────────────────────────────────────────────────────


class TestGetUnitSpec:
    def test_known_group_and_unit_returns_spec(self) -> None:
        spec = get_unit_spec("pressure", "kPa")
        assert spec.scale == pytest.approx(1e-3)
        assert spec.offset == 0.0

    def test_celsius_spec_has_correct_offset(self) -> None:
        spec = get_unit_spec("temperature", "°C")
        assert spec.scale == pytest.approx(1.0)
        assert spec.offset == pytest.approx(-273.15)

    def test_unknown_group_raises_key_error(self) -> None:
        with pytest.raises(KeyError, match="Unknown unit group"):
            get_unit_spec("bogus_group", "Pa")

    def test_unknown_unit_raises_key_error(self) -> None:
        with pytest.raises(KeyError, match="Unknown unit"):
            get_unit_spec("pressure", "atm")


# ── convert_value ─────────────────────────────────────────────────────────────


class TestConvertValue:
    def test_pa_to_kpa(self) -> None:
        assert convert_value(100_000.0, "pressure", {"pressure": "kPa"}) == pytest.approx(100.0)

    def test_pa_to_mpa(self) -> None:
        assert convert_value(1_000_000.0, "pressure", {"pressure": "MPa"}) == pytest.approx(1.0)

    def test_pa_to_bar(self) -> None:
        assert convert_value(100_000.0, "pressure", {"pressure": "bar"}) == pytest.approx(1.0)

    def test_pa_identity(self) -> None:
        assert convert_value(42_000.0, "pressure", {"pressure": "Pa"}) == pytest.approx(42_000.0)

    def test_m_to_um(self) -> None:
        assert convert_value(5.0e-5, "diameter", {"diameter": "μm"}) == pytest.approx(50.0)

    def test_m_to_mm_diameter(self) -> None:
        assert convert_value(1.0e-3, "diameter", {"diameter": "mm"}) == pytest.approx(1.0)

    def test_m_to_nm(self) -> None:
        assert convert_value(1.0e-9, "diameter", {"diameter": "nm"}) == pytest.approx(1.0)

    def test_k_to_celsius(self) -> None:
        assert convert_value(300.0, "temperature", {"temperature": "°C"}) == pytest.approx(26.85)

    def test_k_identity(self) -> None:
        assert convert_value(300.0, "temperature", {"temperature": "K"}) == pytest.approx(300.0)

    def test_zero_celsius(self) -> None:
        assert convert_value(273.15, "temperature", {"temperature": "°C"}) == pytest.approx(0.0)

    def test_boiling_point_celsius(self) -> None:
        assert convert_value(373.15, "temperature", {"temperature": "°C"}) == pytest.approx(100.0)

    def test_fallback_to_default_when_group_absent_from_prefs(self) -> None:
        # Empty prefs → DEFAULT_UNITS["pressure"] = "kPa"
        assert convert_value(100_000.0, "pressure", {}) == pytest.approx(100.0)

    def test_m_to_mm_length(self) -> None:
        assert convert_value(0.1, "length", {"length": "mm"}) == pytest.approx(100.0)

    def test_m2_to_mm2(self) -> None:
        assert convert_value(1.0e-4, "area", {"area": "mm²"}) == pytest.approx(100.0)


# ── convert_series ────────────────────────────────────────────────────────────


class TestConvertSeries:
    def test_empty_list_returns_empty(self) -> None:
        assert convert_series([], "pressure", {"pressure": "kPa"}) == []

    def test_pa_list_to_kpa(self) -> None:
        result = convert_series([100_000.0, 200_000.0], "pressure", {"pressure": "kPa"})
        assert result == pytest.approx([100.0, 200.0])

    def test_temperature_offset_applied(self) -> None:
        result = convert_series([273.15, 373.15], "temperature", {"temperature": "°C"})
        assert result == pytest.approx([0.0, 100.0])

    def test_diameter_m_to_um(self) -> None:
        result = convert_series([1.0e-6, 5.0e-5], "diameter", {"diameter": "μm"})
        assert result == pytest.approx([1.0, 50.0])

    def test_single_element(self) -> None:
        result = convert_series([100_000.0], "pressure", {"pressure": "kPa"})
        assert result == pytest.approx([100.0])

    def test_identity_with_si_unit(self) -> None:
        result = convert_series([1.0, 2.0, 3.0], "pressure", {"pressure": "Pa"})
        assert result == pytest.approx([1.0, 2.0, 3.0])


# ── display_unit_label ────────────────────────────────────────────────────────


class TestDisplayUnitLabel:
    def test_prefs_override(self) -> None:
        assert display_unit_label("pressure", {"pressure": "MPa"}) == "MPa"

    def test_default_fallback_for_absent_group(self) -> None:
        assert display_unit_label("pressure", {}) == "kPa"

    def test_diameter_default_is_um(self) -> None:
        assert display_unit_label("diameter", {}) == "μm"

    def test_temperature_default_is_k(self) -> None:
        assert display_unit_label("temperature", {}) == "K"

    def test_celsius_pref(self) -> None:
        assert display_unit_label("temperature", {"temperature": "°C"}) == "°C"


# ── field_display_label ───────────────────────────────────────────────────────


class TestFieldDisplayLabel:
    def test_pressure_field_gets_kpa_suffix(self) -> None:
        label = field_display_label("pressure", {"pressure": "kPa"})
        assert label == "pressure [kPa]"

    def test_pressure_field_gets_mpa_suffix(self) -> None:
        label = field_display_label("pressure", {"pressure": "MPa"})
        assert label == "pressure [MPa]"

    def test_diameter_field_gets_um_suffix(self) -> None:
        label = field_display_label("droplet_mean_diameter", {"diameter": "μm"})
        assert label == "droplet_mean_diameter [μm]"

    def test_mach_number_no_suffix(self) -> None:
        label = field_display_label("Mach_number", {"pressure": "kPa"})
        assert label == "Mach_number"

    def test_weber_number_no_suffix(self) -> None:
        assert field_display_label("Weber_number", {}) == "Weber_number"

    def test_breakup_flag_no_suffix(self) -> None:
        assert field_display_label("breakup_flag", {"pressure": "MPa"}) == "breakup_flag"

    def test_dimensionless_reynolds_no_suffix(self) -> None:
        assert field_display_label("droplet_reynolds_number", {"pressure": "kPa"}) == "droplet_reynolds_number"


# ── FIELD_UNIT_GROUP completeness ─────────────────────────────────────────────


class TestFieldUnitGroup:
    def test_all_group_references_are_valid(self) -> None:
        for field, group in FIELD_UNIT_GROUP.items():
            if group is not None:
                assert group in UNIT_GROUPS, f"Field {field!r} maps to unknown group {group!r}"

    def test_mach_number_is_dimensionless(self) -> None:
        assert FIELD_UNIT_GROUP["Mach_number"] is None

    def test_weber_number_is_dimensionless(self) -> None:
        assert FIELD_UNIT_GROUP["Weber_number"] is None

    def test_breakup_flag_is_dimensionless(self) -> None:
        assert FIELD_UNIT_GROUP["breakup_flag"] is None

    def test_pressure_maps_to_pressure_group(self) -> None:
        assert FIELD_UNIT_GROUP["pressure"] == "pressure"

    def test_diameter_fields_map_to_diameter_group(self) -> None:
        assert FIELD_UNIT_GROUP["droplet_mean_diameter"] == "diameter"
        assert FIELD_UNIT_GROUP["droplet_maximum_diameter"] == "diameter"

    def test_velocity_fields_map_to_velocity_group(self) -> None:
        assert FIELD_UNIT_GROUP["working_fluid_velocity"] == "velocity"
        assert FIELD_UNIT_GROUP["droplet_velocity"] == "velocity"
        assert FIELD_UNIT_GROUP["slip_velocity"] == "velocity"

    def test_x_maps_to_length_group(self) -> None:
        assert FIELD_UNIT_GROUP["x"] == "length"

    def test_A_maps_to_area_group(self) -> None:
        assert FIELD_UNIT_GROUP["A"] == "area"


# ── GUIState unit fields and unit_preferences() ───────────────────────────────


class TestGUIStateUnitFields:
    def test_default_pressure_is_kpa(self) -> None:
        assert GUIState().unit_pressure == "kPa"

    def test_default_diameter_is_um(self) -> None:
        assert GUIState().unit_diameter == "μm"

    def test_default_temperature_is_k(self) -> None:
        assert GUIState().unit_temperature == "K"

    def test_default_velocity_is_ms(self) -> None:
        assert GUIState().unit_velocity == "m/s"

    def test_default_length_is_m(self) -> None:
        assert GUIState().unit_length == "m"

    def test_default_area_is_m2(self) -> None:
        assert GUIState().unit_area == "m²"

    def test_default_density_is_kgm3(self) -> None:
        assert GUIState().unit_density == "kg/m³"

    def test_all_defaults_match_DEFAULT_UNITS(self) -> None:
        state = GUIState()
        prefs = state.unit_preferences()
        for group, expected in DEFAULT_UNITS.items():
            assert prefs[group] == expected, (
                f"Group {group!r}: expected {expected!r}, got {prefs[group]!r}"
            )

    def test_unit_preferences_returns_all_seven_groups(self) -> None:
        prefs = GUIState().unit_preferences()
        for group in ("pressure", "temperature", "velocity", "diameter", "length", "area", "density"):
            assert group in prefs

    def test_mutation_reflected_in_unit_preferences(self) -> None:
        state = GUIState()
        state.unit_pressure = "Pa"
        assert state.unit_preferences()["pressure"] == "Pa"

    def test_temperature_mutation_celsius(self) -> None:
        state = GUIState()
        state.unit_temperature = "°C"
        assert state.unit_preferences()["temperature"] == "°C"

    def test_diameter_mutation_mm(self) -> None:
        state = GUIState()
        state.unit_diameter = "mm"
        assert state.unit_preferences()["diameter"] == "mm"


# ── unit_settings_page helpers ────────────────────────────────────────────────


class TestUnitSettingsPageHelpers:
    # get_unit_choices

    def test_get_unit_choices_pressure_contains_expected(self) -> None:
        choices = get_unit_choices("pressure")
        for unit in ("Pa", "kPa", "MPa", "bar"):
            assert unit in choices

    def test_get_unit_choices_diameter_contains_expected(self) -> None:
        choices = get_unit_choices("diameter")
        for unit in ("m", "mm", "μm", "nm"):
            assert unit in choices

    def test_get_unit_choices_temperature_contains_celsius(self) -> None:
        assert "°C" in get_unit_choices("temperature")

    def test_get_unit_choices_unknown_group_raises(self) -> None:
        with pytest.raises(KeyError):
            get_unit_choices("bogus_group")

    # apply_unit_preference

    def test_apply_pressure_to_pa(self) -> None:
        state = GUIState()
        apply_unit_preference(state, "pressure", "Pa")
        assert state.unit_pressure == "Pa"

    def test_apply_diameter_to_mm(self) -> None:
        state = GUIState()
        apply_unit_preference(state, "diameter", "mm")
        assert state.unit_diameter == "mm"

    def test_apply_temperature_to_celsius(self) -> None:
        state = GUIState()
        apply_unit_preference(state, "temperature", "°C")
        assert state.unit_temperature == "°C"

    def test_apply_unknown_group_raises(self) -> None:
        state = GUIState()
        with pytest.raises(KeyError):
            apply_unit_preference(state, "bogus_group", "Pa")

    def test_apply_unknown_unit_raises(self) -> None:
        state = GUIState()
        with pytest.raises(KeyError):
            apply_unit_preference(state, "pressure", "atm")

    # get_unit_preference

    def test_get_returns_state_field(self) -> None:
        state = GUIState()
        state.unit_pressure = "MPa"
        assert get_unit_preference(state, "pressure") == "MPa"

    def test_get_returns_default_for_unmodified_state(self) -> None:
        state = GUIState()
        assert get_unit_preference(state, "diameter") == "μm"

    def test_get_unknown_group_returns_empty_string(self) -> None:
        state = GUIState()
        assert get_unit_preference(state, "bogus_group") == ""


# ── extract_plot_series with unit_preferences ─────────────────────────────────


class TestExtractPlotSeriesWithUnits:
    def test_all_required_keys_present_no_prefs(self, sample_result: SimulationResult) -> None:
        series = extract_plot_series(sample_result)
        expected_keys = {
            "pressure", "temperature", "working_fluid_velocity", "droplet_velocity",
            "slip_velocity",
            "Mach_number", "droplet_mean_diameter", "droplet_maximum_diameter", "Weber_number",
        }
        assert set(series.keys()) == expected_keys

    def test_si_values_returned_when_no_prefs(self, sample_result: SimulationResult) -> None:
        series = extract_plot_series(sample_result)
        # No prefs: pressure values stay in Pa
        assert series["pressure"]["y"] == pytest.approx([100_000.0, 95_000.0])

    def test_x_axis_in_si_when_no_prefs(self, sample_result: SimulationResult) -> None:
        series = extract_plot_series(sample_result)
        assert series["pressure"]["x"] == pytest.approx([0.0, 0.1])

    def test_pressure_converted_to_kpa_with_full_prefs(
        self, sample_result: SimulationResult, full_prefs: dict
    ) -> None:
        series = extract_plot_series(sample_result, full_prefs)
        assert series["pressure"]["y"] == pytest.approx([100.0, 95.0])

    def test_pressure_ylabel_contains_kpa(
        self, sample_result: SimulationResult, full_prefs: dict
    ) -> None:
        series = extract_plot_series(sample_result, full_prefs)
        assert "kPa" in series["pressure"]["ylabel"]

    def test_diameter_converted_to_um(
        self, sample_result: SimulationResult, full_prefs: dict
    ) -> None:
        series = extract_plot_series(sample_result, full_prefs)
        # 5e-5 m → 50 μm, 4e-5 m → 40 μm
        assert series["droplet_mean_diameter"]["y"] == pytest.approx([50.0, 40.0])

    def test_mach_number_unchanged_dimensionless(
        self, sample_result: SimulationResult, full_prefs: dict
    ) -> None:
        series = extract_plot_series(sample_result, full_prefs)
        assert series["Mach_number"]["y"] == pytest.approx([0.2, 0.3])

    def test_x_axis_converted_to_mm(self, sample_result: SimulationResult) -> None:
        prefs = {
            "pressure": "kPa", "temperature": "K", "velocity": "m/s",
            "diameter": "μm", "length": "mm", "area": "m²", "density": "kg/m³",
        }
        series = extract_plot_series(sample_result, prefs)
        # 0.0 m → 0.0 mm, 0.1 m → 100.0 mm
        assert series["pressure"]["x"] == pytest.approx([0.0, 100.0])

    def test_x_label_reflects_mm(self, sample_result: SimulationResult) -> None:
        prefs = {
            "pressure": "kPa", "temperature": "K", "velocity": "m/s",
            "diameter": "μm", "length": "mm", "area": "m²", "density": "kg/m³",
        }
        series = extract_plot_series(sample_result, prefs)
        assert "mm" in series["pressure"]["x_label"]

    def test_temperature_converted_to_celsius(self, sample_result: SimulationResult) -> None:
        prefs = {
            "pressure": "kPa", "temperature": "°C", "velocity": "m/s",
            "diameter": "μm", "length": "m", "area": "m²", "density": "kg/m³",
        }
        series = extract_plot_series(sample_result, prefs)
        # 300 K → 26.85 °C, 295 K → 21.85 °C
        assert series["temperature"]["y"] == pytest.approx([26.85, 21.85])

    def test_empty_prefs_uses_default_units(self, sample_result: SimulationResult) -> None:
        # {} → DEFAULT_UNITS → pressure in kPa
        series = extract_plot_series(sample_result, {})
        assert series["pressure"]["y"] == pytest.approx([100.0, 95.0])

    def test_all_required_keys_present_with_full_prefs(
        self, sample_result: SimulationResult, full_prefs: dict
    ) -> None:
        series = extract_plot_series(sample_result, full_prefs)
        for key in ("pressure", "temperature", "working_fluid_velocity", "droplet_velocity",
                    "Mach_number", "droplet_mean_diameter", "droplet_maximum_diameter", "Weber_number"):
            assert key in series


# ── result_to_table_rows with unit_preferences ────────────────────────────────


class TestResultToTableRowsWithUnits:
    # Backward-compat: no prefs

    def test_no_prefs_plain_keys(self, sample_result: SimulationResult) -> None:
        rows = result_to_table_rows(sample_result)
        assert "pressure" in rows[0]
        assert "temperature" in rows[0]

    def test_no_prefs_si_pressure(self, sample_result: SimulationResult) -> None:
        rows = result_to_table_rows(sample_result)
        assert rows[0]["pressure"] == pytest.approx(100_000.0)

    def test_no_prefs_si_temperature(self, sample_result: SimulationResult) -> None:
        rows = result_to_table_rows(sample_result)
        assert rows[0]["temperature"] == pytest.approx(300.0)

    def test_no_prefs_breakup_flag_accessible(self, sample_result: SimulationResult) -> None:
        rows = result_to_table_rows(sample_result)
        assert rows[1]["breakup_flag"] is True

    def test_no_prefs_correct_row_count(self, sample_result: SimulationResult) -> None:
        rows = result_to_table_rows(sample_result)
        assert len(rows) == 2

    # With prefs

    def test_with_prefs_pressure_converted_to_kpa(
        self, sample_result: SimulationResult, full_prefs: dict
    ) -> None:
        rows = result_to_table_rows(sample_result, full_prefs)
        assert rows[0]["pressure [kPa]"] == pytest.approx(100.0)

    def test_with_prefs_plain_pressure_key_absent(
        self, sample_result: SimulationResult, full_prefs: dict
    ) -> None:
        rows = result_to_table_rows(sample_result, full_prefs)
        assert "pressure" not in rows[0]

    def test_with_prefs_diameter_converted_to_um(
        self, sample_result: SimulationResult, full_prefs: dict
    ) -> None:
        rows = result_to_table_rows(sample_result, full_prefs)
        # 5e-5 m → 50 μm
        assert rows[0]["droplet_mean_diameter [μm]"] == pytest.approx(50.0)

    def test_with_prefs_breakup_flag_key_unchanged(
        self, sample_result: SimulationResult, full_prefs: dict
    ) -> None:
        rows = result_to_table_rows(sample_result, full_prefs)
        # breakup_flag is boolean (None group) → always plain key
        assert rows[1]["breakup_flag"] is True

    def test_with_prefs_mach_number_key_unchanged(
        self, sample_result: SimulationResult, full_prefs: dict
    ) -> None:
        rows = result_to_table_rows(sample_result, full_prefs)
        # Mach_number is dimensionless → no unit suffix
        assert "Mach_number" in rows[0]

    def test_with_prefs_correct_row_count(
        self, sample_result: SimulationResult, full_prefs: dict
    ) -> None:
        rows = result_to_table_rows(sample_result, full_prefs)
        assert len(rows) == 2

    def test_with_prefs_second_row_pressure(
        self, sample_result: SimulationResult, full_prefs: dict
    ) -> None:
        rows = result_to_table_rows(sample_result, full_prefs)
        assert rows[1]["pressure [kPa]"] == pytest.approx(95.0)

    # CSV content

    def test_csv_no_prefs_has_plain_headers(self, sample_result: SimulationResult) -> None:
        rows = result_to_table_rows(sample_result)
        csv_text = generate_csv_content(rows)
        assert "pressure" in csv_text
        assert "Weber_number" in csv_text

    def test_csv_with_prefs_has_unit_headers(
        self, sample_result: SimulationResult, full_prefs: dict
    ) -> None:
        rows = result_to_table_rows(sample_result, full_prefs)
        csv_text = generate_csv_content(rows)
        assert "pressure [kPa]" in csv_text
        assert "droplet_mean_diameter [μm]" in csv_text

    def test_csv_with_prefs_dimensionless_headers_unchanged(
        self, sample_result: SimulationResult, full_prefs: dict
    ) -> None:
        rows = result_to_table_rows(sample_result, full_prefs)
        csv_text = generate_csv_content(rows)
        assert "Mach_number" in csv_text
        assert "Weber_number" in csv_text
        assert "breakup_flag" in csv_text
