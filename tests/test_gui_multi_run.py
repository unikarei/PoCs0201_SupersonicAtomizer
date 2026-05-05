from __future__ import annotations

import sys
import time
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.app.services import SimulationRunResult
from supersonic_atomizer.domain import RunDiagnostics, SimulationResult
from supersonic_atomizer.domain.state_models import (
    DropletSolution,
    DropletState,
    GasSolution,
    GasState,
    ThermoState,
)
from supersonic_atomizer.gui.multi_run import (
    MAX_SWEEP_RUNS,
    execute_expanded_runs,
    expand_multi_value_config,
    parse_numeric_token_list,
)
from supersonic_atomizer.gui.pages.post_graphs import extract_overlay_plot_series
from supersonic_atomizer.gui.pages.post_table import aggregate_result_to_table_rows


def _build_simulation_result(*, pt_in: float) -> SimulationResult:
    thermo_a = ThermoState(pressure=pt_in * 0.8, temperature=400.0, density=1.2, enthalpy=1.0, sound_speed=340.0)
    thermo_b = ThermoState(pressure=pt_in * 0.6, temperature=390.0, density=1.0, enthalpy=1.0, sound_speed=335.0)

    gas_states = (
        GasState(x=0.0, area=1.0e-4, pressure=pt_in * 0.8, temperature=400.0, density=1.2, velocity=120.0, mach_number=0.4, thermo_state=thermo_a),
        GasState(x=0.1, area=8.0e-5, pressure=pt_in * 0.6, temperature=390.0, density=1.0, velocity=220.0, mach_number=0.75, thermo_state=thermo_b),
    )
    gas_solution = GasSolution(
        states=gas_states,
        x_values=(0.0, 0.1),
        area_values=(1.0e-4, 8.0e-5),
        pressure_values=(pt_in * 0.8, pt_in * 0.6),
        temperature_values=(400.0, 390.0),
        density_values=(1.2, 1.0),
        velocity_values=(120.0, 220.0),
        mach_number_values=(0.4, 0.75),
    )

    droplet_states = (
        DropletState(x=0.0, velocity=15.0, slip_velocity=105.0, mean_diameter=50e-6, maximum_diameter=100e-6, weber_number=10.0, reynolds_number=100.0, breakup_triggered=False),
        DropletState(x=0.1, velocity=40.0, slip_velocity=180.0, mean_diameter=40e-6, maximum_diameter=80e-6, weber_number=16.0, reynolds_number=140.0, breakup_triggered=True),
    )
    droplet_solution = DropletSolution(
        states=droplet_states,
        x_values=(0.0, 0.1),
        velocity_values=(15.0, 40.0),
        slip_velocity_values=(105.0, 180.0),
        mean_diameter_values=(50e-6, 40e-6),
        maximum_diameter_values=(100e-6, 80e-6),
        weber_number_values=(10.0, 16.0),
        reynolds_number_values=(100.0, 140.0),
        breakup_flags=(False, True),
    )

    diagnostics = RunDiagnostics(status="success")
    return SimulationResult(
        case_name="gui_case",
        working_fluid="air",
        gas_solution=gas_solution,
        droplet_solution=droplet_solution,
        diagnostics=diagnostics,
    )


def _build_completed_run_result(case_path: str, *, pt_in: float) -> SimulationRunResult:
    return SimulationRunResult(
        status="completed",
        case_path=case_path,
        simulation_result=_build_simulation_result(pt_in=pt_in),
    )


def _base_gui_config() -> dict[str, object]:
    return {
        "fluid": {"working_fluid": "air"},
        "boundary_conditions": {
            "Pt_in": "200000",
            "Tt_in": "400",
            "Ps_out": "101325",
        },
        "geometry": {
            "x_start": 0.0,
            "x_end": 0.1,
            "n_cells": 20,
            "area_distribution": {
                "type": "table",
                "x": [0.0, 0.1],
                "A": [1.0e-4, 8.0e-5],
            },
        },
        "droplet_injection": {
            "droplet_velocity_in": "10",
            "droplet_diameter_mean_in": "5e-05",
            "droplet_diameter_max_in": "1e-04",
        },
        "models": {
            "breakup_model": "weber_critical",
            "critical_weber_number": "12",
            "breakup_factor_mean": "0.5",
            "breakup_factor_max": "0.5",
        },
        "outputs": {
            "output_directory": "outputs",
            "write_csv": True,
            "write_json": True,
            "generate_plots": True,
        },
    }


class TestMultiRunParsing:

    def test_parse_numeric_token_list_supports_multiple_delimiters(self):
        values = parse_numeric_token_list("1, 2 3;4\n5，6、7")
        assert values == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]

    def test_expand_multi_value_config_cartesian_product(self):
        config = _base_gui_config()
        config["boundary_conditions"]["Pt_in"] = "200000, 220000"
        config["models"]["critical_weber_number"] = "12 14"

        expanded = expand_multi_value_config(case_name="demo_case", raw_config=config)

        assert len(expanded) == 4
        assert all("Pt_in=" in run.run_label for run in expanded)
        assert any("critical_weber_number=14" in run.run_label for run in expanded)
        assert all(run.config["outputs"]["write_csv"] is True for run in expanded)
        assert all(run.config["outputs"]["write_json"] is True for run in expanded)
        assert all(run.config["outputs"]["generate_plots"] is True for run in expanded)

    def test_expand_multi_value_config_rejects_excessive_run_counts(self):
        config = _base_gui_config()
        config["boundary_conditions"]["Pt_in"] = " ".join(str(100000 + i) for i in range(MAX_SWEEP_RUNS + 1))

        with pytest.raises(ValueError, match="exceeding the limit"):
            expand_multi_value_config(case_name="demo_case", raw_config=config)

    def test_expand_multi_value_config_supports_water_mass_flow_rate_sweep(self):
        config = _base_gui_config()
        config["droplet_injection"]["water_mass_flow_rate"] = "0.1, 0.2"

        expanded = expand_multi_value_config(case_name="demo_case", raw_config=config)

        assert len(expanded) == 2
        assert expanded[0].config["droplet_injection"]["water_mass_flow_rate"] == 0.1
        assert expanded[1].config["droplet_injection"]["water_mass_flow_rate"] == 0.2

    def test_expand_multi_value_config_supports_water_mass_flow_rate_percent_sweep(self):
        config = _base_gui_config()
        config["droplet_injection"]["water_mass_flow_rate_percent"] = "2.5, 5.0"

        expanded = expand_multi_value_config(case_name="demo_case", raw_config=config)

        assert len(expanded) == 2
        assert expanded[0].config["droplet_injection"]["water_mass_flow_rate_percent"] == 2.5
        assert expanded[1].config["droplet_injection"]["water_mass_flow_rate_percent"] == 5.0

    def test_expand_multi_value_config_normalizes_optional_model_numeric_fields(self):
        config = _base_gui_config()
        config["models"]["breakup_model"] = "bag_stripping"
        config["models"]["khrt_B0"] = "0.61"
        config["models"]["khrt_B1"] = ""
        config["models"]["khrt_Crt"] = None

        expanded = expand_multi_value_config(case_name="demo_case", raw_config=config)

        assert len(expanded) == 1
        models = expanded[0].config["models"]
        assert models["khrt_B0"] == pytest.approx(0.61)
        assert "khrt_B1" not in models
        assert "khrt_Crt" not in models

    def test_expand_multi_value_config_drops_blank_optional_liquid_jet_fields(self):
        config = _base_gui_config()
        config["droplet_injection"]["injection_mode"] = "droplet_injection"
        config["droplet_injection"]["liquid_jet_diameter"] = None
        config["droplet_injection"]["liquid_mass_flow_rate"] = ""
        config["droplet_injection"]["liquid_velocity"] = "   "
        config["droplet_injection"]["surface_tension"] = "0.072"
        config["droplet_injection"]["primary_breakup_model"] = ""

        expanded = expand_multi_value_config(case_name="demo_case", raw_config=config)

        assert len(expanded) == 1
        di = expanded[0].config["droplet_injection"]
        assert "liquid_jet_diameter" not in di
        assert "liquid_mass_flow_rate" not in di
        assert "liquid_velocity" not in di
        assert di["surface_tension"] == pytest.approx(0.072)
        assert "primary_breakup_model" not in di

    def test_expand_multi_value_config_normalizes_legacy_geometry_format(self):
        config = _base_gui_config()
        # Replace new-format geometry with legacy format
        config["geometry"] = {
            "x_start": 0.0,
            "x_end": 0.5,
            "num_cells": 80,
            "area_table": [
                {"x": 0.0,  "A": 0.01},
                {"x": 0.25, "A": 0.005},
                {"x": 0.5,  "A": 0.01},
            ],
        }

        expanded = expand_multi_value_config(case_name="demo_case", raw_config=config)

        assert len(expanded) == 1
        geo = expanded[0].config["geometry"]
        assert geo["n_cells"] == 80
        assert "num_cells" not in geo
        assert "area_table" not in geo
        assert geo["area_distribution"]["type"] == "table"
        assert geo["area_distribution"]["x"] == [0.0, 0.25, 0.5]
        assert geo["area_distribution"]["A"] == [0.01, 0.005, 0.01]

    def test_execute_expanded_runs_writes_solver_compatible_yaml_snapshots(self):
        config = _base_gui_config()
        config["boundary_conditions"]["Pt_in"] = "200000, 230000"
        expanded = expand_multi_value_config(case_name="demo_case", raw_config=config)

        seen_pressures: list[float] = []

        def fake_runner(case_path: str) -> SimulationRunResult:
            snapshot = yaml.safe_load(Path(case_path).read_text(encoding="utf-8"))
            assert snapshot["outputs"]["write_csv"] is True
            assert snapshot["outputs"]["write_json"] is True
            assert snapshot["outputs"]["generate_plots"] is True
            pt_in = float(snapshot["boundary_conditions"]["Pt_in"])
            seen_pressures.append(pt_in)
            return _build_completed_run_result(case_path, pt_in=pt_in)

        batch_result = execute_expanded_runs(
            case_name="demo_case",
            expanded_runs=expanded,
            runner=fake_runner,
        )

        assert batch_result.run_count == 2
        assert seen_pressures == [200000.0, 230000.0]

    def test_execute_expanded_runs_keeps_project_case_identity_in_snapshot_path(self):
        config = _base_gui_config()
        expanded = expand_multi_value_config(case_name="demo_case", raw_config=config)

        seen_paths: list[Path] = []

        def fake_runner(case_path: str) -> SimulationRunResult:
            p = Path(case_path)
            seen_paths.append(p)
            return _build_completed_run_result(case_path, pt_in=200000.0)

        execute_expanded_runs(
            case_name="demo_case",
            project_name="proj_demo",
            expanded_runs=expanded,
            runner=fake_runner,
        )

        assert seen_paths
        assert all(p.parent.name == "proj_demo" for p in seen_paths)
        assert all(p.stem == "demo_case" for p in seen_paths)


class TestOverlayHelpers:

    def test_extract_overlay_plot_series_contains_multiple_runs_and_slip_velocity(self):
        labeled_results = [
            ("Pt_in=200000", _build_simulation_result(pt_in=200000.0)),
            ("Pt_in=220000", _build_simulation_result(pt_in=220000.0)),
        ]

        overlay = extract_overlay_plot_series(labeled_results)

        assert "area_profile" in overlay
        assert "pressure" in overlay
        assert "slip_velocity" in overlay
        assert len(overlay["pressure"]["series"]) == 2
        assert overlay["pressure"]["series"][0]["label"] == "Pt_in=200000"

    def test_aggregate_result_to_table_rows_adds_run_label(self):
        labeled_results = [
            ("Pt_in=200000", _build_simulation_result(pt_in=200000.0)),
            ("Pt_in=220000", _build_simulation_result(pt_in=220000.0)),
        ]

        rows = aggregate_result_to_table_rows(labeled_results)

        assert len(rows) == 4
        assert rows[0]["run_label"] == "Pt_in=200000"
        assert "pressure" in rows[0]


@pytest.fixture(scope="module")
def app_with_tmp_store(tmp_path_factory):
    from supersonic_atomizer.gui.case_store import CaseStore
    from supersonic_atomizer.gui.fastapi_app import create_app

    tmp_dir = tmp_path_factory.mktemp("fastapi_multi_run_cases")
    store = CaseStore(cases_dir=tmp_dir)

    def _get_store_func():
        return store

    app = create_app()
    import supersonic_atomizer.gui.routers.cases_router as _cr
    import supersonic_atomizer.gui.routers.simulation_router as _sr

    original_cr = _cr._get_store
    original_sr_cls = _sr.CaseStore
    _cr._get_store = _get_store_func
    _sr.CaseStore = lambda: store
    yield app, tmp_dir
    _cr._get_store = original_cr
    _sr.CaseStore = original_sr_cls


@pytest.fixture(scope="module")
def client(app_with_tmp_store):
    from fastapi.testclient import TestClient

    app, _ = app_with_tmp_store
    with TestClient(app, raise_server_exceptions=True) as tc:
        yield tc


class TestFastApiMultiRunFlow:

    def test_run_parameter_sweep_returns_aggregated_overlay_results(self, client, monkeypatch):
        client.post("/api/cases/", json={"name": "multi_run_case"})

        def fake_runner(case_path: str) -> SimulationRunResult:
            snapshot = yaml.safe_load(Path(case_path).read_text(encoding="utf-8"))
            pt_in = float(snapshot["boundary_conditions"]["Pt_in"])
            return _build_completed_run_result(case_path, pt_in=pt_in)

        monkeypatch.setattr(
            "supersonic_atomizer.gui.routers.simulation_router._bridge",
            MagicMock(run_simulation_sync=fake_runner),
        )

        config = _base_gui_config()
        config["boundary_conditions"]["Pt_in"] = "200000, 220000"

        run_response = client.post(
            "/api/simulation/run",
            json={"case_name": "multi_run_case", "config": config},
        )
        assert run_response.status_code == 200
        job_id = run_response.json()["job_id"]
        uuid.UUID(job_id)

        status_response = None
        for _ in range(30):
            status_response = client.get(f"/api/simulation/status/{job_id}")
            assert status_response.status_code == 200
            if status_response.json()["status"] != "running":
                break
            time.sleep(0.1)

        assert status_response is not None
        assert status_response.json()["status"] == "completed"

        result_response = client.get(f"/api/simulation/result/{job_id}")
        assert result_response.status_code == 200
        payload = result_response.json()

        assert payload["run_count"] == 2
        assert "pressure" in payload["plots"]
        assert payload["plot_fields"][0] == "area_profile"
        assert "slip_velocity" in payload["plot_fields"]
        assert payload["table_rows"]
        assert "run_label" in payload["table_rows"][0]
        assert "Pt_in=200000" in payload["csv"]
