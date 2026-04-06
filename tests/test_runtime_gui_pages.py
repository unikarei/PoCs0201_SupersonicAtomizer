"""Tests for GUI helper logic added in P23-T04 through P23-T10.

These tests exercise pure-Python helper functions only.
No live Streamlit session or browser is required.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from supersonic_atomizer.app.services import SimulationRunResult
from supersonic_atomizer.domain import (
    DropletSolution,
    DropletState,
    GasSolution,
    GasState,
    RunDiagnostics,
    SimulationResult,
    ThermoState,
)
from supersonic_atomizer.gui.case_store import CaseStore
from supersonic_atomizer.gui.pages.post_graphs import extract_plot_series
from supersonic_atomizer.gui.pages.post_table import generate_csv_content, result_to_table_rows
from supersonic_atomizer.gui.pages.pre_conditions import (
    state_to_conditions_config,
    validate_conditions,
)
from supersonic_atomizer.gui.pages.pre_grid import state_to_geometry_config, validate_area_table
from supersonic_atomizer.gui.pages.solve import (
    build_case_config_from_state,
    persist_state_to_case,
    validate_ready_to_run,
)
from supersonic_atomizer.gui.panels.case_panel import (
    apply_case_selection,
    apply_new_case,
    populate_state_from_config,
)
from supersonic_atomizer.gui.state import GUIState


@pytest.fixture()
def sample_state() -> GUIState:
    state = GUIState()
    state.active_case_name = "alpha"
    state.active_case_path = "cases/alpha.yaml"
    return state


@pytest.fixture()
def case_store(tmp_path) -> CaseStore:
    return CaseStore(cases_dir=tmp_path / "cases")


@pytest.fixture()
def sample_result() -> SimulationResult:
    thermo = ThermoState(pressure=100000.0, temperature=300.0, density=1.2, enthalpy=1.0, sound_speed=340.0)
    gas_states = (
        GasState(0.0, 1.0e-4, 100000.0, 300.0, 1.2, 50.0, 0.2, thermo),
        GasState(0.1, 8.0e-5, 95000.0, 295.0, 1.15, 80.0, 0.3, thermo),
    )
    gas = GasSolution(
        states=gas_states,
        x_values=(0.0, 0.1),
        area_values=(1.0e-4, 8.0e-5),
        pressure_values=(100000.0, 95000.0),
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
        case_name="alpha",
        working_fluid="air",
        gas_solution=gas,
        droplet_solution=droplet,
        diagnostics=RunDiagnostics(status="completed"),
    )


def test_populate_state_from_config_updates_fields(sample_state: GUIState) -> None:
    config = {
        "fluid": {"working_fluid": "steam", "inlet_wetness": 0.1},
        "boundary_conditions": {"Pt_in": 300000.0, "Tt_in": 500.0, "Ps_out": 150000.0},
        "droplet_injection": {
            "droplet_velocity_in": 25.0,
            "droplet_diameter_mean_in": 9.0e-5,
            "droplet_diameter_max_in": 1.5e-4,
        },
        "models": {"critical_weber_number": 15.0, "breakup_factor_mean": 0.6, "breakup_factor_max": 0.7},
        "geometry": {
            "x_start": 0.0,
            "x_end": 0.2,
            "n_cells": 50,
            "area_distribution": {"type": "table", "x": [0.0, 0.2], "A": [1.0e-4, 0.8e-4]},
        },
    }
    populate_state_from_config(sample_state, config)
    assert sample_state.working_fluid == "steam"
    assert sample_state.inlet_wetness == pytest.approx(0.1)
    assert sample_state.n_cells == 50
    assert len(sample_state.area_table) == 2


def test_apply_new_case_sets_active_state(sample_state: GUIState, case_store: CaseStore) -> None:
    path = apply_new_case(sample_state, "new_case", case_store)
    assert path.is_file()
    assert sample_state.active_case_name == "new_case"
    assert sample_state.active_case_path.endswith("new_case.yaml")


def test_apply_case_selection_loads_state(sample_state: GUIState, case_store: CaseStore) -> None:
    case_store.create("sel_case", template={
        "fluid": {"working_fluid": "steam"},
        "boundary_conditions": {"Pt_in": 250000.0, "Tt_in": 450.0, "Ps_out": 120000.0},
    })
    apply_case_selection(sample_state, "sel_case", case_store)
    assert sample_state.active_case_name == "sel_case"
    assert sample_state.working_fluid == "steam"
    assert sample_state.inlet_total_pressure == pytest.approx(250000.0)


def test_validate_conditions_success(sample_state: GUIState) -> None:
    assert validate_conditions(sample_state) == []


def test_validate_conditions_multiple_errors(sample_state: GUIState) -> None:
    sample_state.working_fluid = "bad"
    sample_state.inlet_total_pressure = -1.0
    sample_state.droplet_diameter_max_in = 0.0
    errors = validate_conditions(sample_state)
    assert len(errors) >= 3


def test_state_to_conditions_config_structure(sample_state: GUIState) -> None:
    config = state_to_conditions_config(sample_state)
    assert set(config.keys()) == {"fluid", "boundary_conditions", "droplet_injection", "models"}
    assert config["fluid"]["working_fluid"] == "air"


def test_validate_area_table_success(sample_state: GUIState) -> None:
    assert validate_area_table(sample_state.area_table) == []


def test_validate_area_table_errors() -> None:
    errors = validate_area_table([
        {"x": 0.0, "A": 1.0e-4},
        {"x": 0.0, "A": -1.0e-4},
    ])
    assert len(errors) >= 2


def test_state_to_geometry_config_structure(sample_state: GUIState) -> None:
    config = state_to_geometry_config(sample_state)
    assert "geometry" in config
    assert config["geometry"]["area_distribution"]["type"] == "table"


def test_build_case_config_from_state_contains_sections(sample_state: GUIState) -> None:
    config = build_case_config_from_state(sample_state)
    for key in ("fluid", "boundary_conditions", "droplet_injection", "models", "geometry", "outputs"):
        assert key in config


def test_validate_ready_to_run_success(sample_state: GUIState) -> None:
    assert validate_ready_to_run(sample_state) == []


def test_validate_ready_to_run_fails_without_case() -> None:
    state = GUIState()
    errors = validate_ready_to_run(state)
    assert any("No active case" in err for err in errors)


def test_persist_state_to_case_writes_yaml(sample_state: GUIState, case_store: CaseStore) -> None:
    path = persist_state_to_case(sample_state, case_store)
    assert path.is_file()
    loaded = case_store.load("alpha")
    assert loaded["fluid"]["working_fluid"] == "air"


def test_extract_plot_series(sample_result: SimulationResult) -> None:
    series = extract_plot_series(sample_result)
    assert set(series.keys()) == {
        "pressure",
        "temperature",
        "working_fluid_velocity",
        "droplet_velocity",
        "Mach_number",
        "droplet_mean_diameter",
        "droplet_maximum_diameter",
        "Weber_number",
    }
    assert series["pressure"]["x"] == [0.0, 0.1]


def test_result_to_table_rows(sample_result: SimulationResult) -> None:
    rows = result_to_table_rows(sample_result)
    assert len(rows) == 2
    assert rows[1]["breakup_flag"] is True


def test_generate_csv_content(sample_result: SimulationResult) -> None:
    rows = result_to_table_rows(sample_result)
    csv_text = generate_csv_content(rows)
    assert "pressure" in csv_text
    assert "Weber_number" in csv_text
