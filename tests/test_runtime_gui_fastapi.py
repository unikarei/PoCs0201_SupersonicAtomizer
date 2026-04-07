"""P25-T07 — FastAPI GUI tests.

Coverage
--------
Unit tests:
  - job_store.JobStore — create, mark_complete, mark_failed, get, thread-safety
  - session_store.SessionStore — get_or_create, get, delete
  - plot_utils.figure_to_base64 / figure_to_data_url
  - schemas — Pydantic model instantiation and validation
  - fastapi_app.create_app — returns FastAPI instance

API endpoint tests (using httpx.AsyncClient / TestClient):
  - GET  /              → HTML 200
  - GET  /api/cases/    → list
  - POST /api/cases/    → create
  - GET  /api/cases/{n} → load
  - PUT  /api/cases/{n} → save
  - DELETE /api/cases/{n} → delete 204
  - POST /api/simulation/run → job_id (with mocked bridge)
  - GET  /api/simulation/status/{id} → status
  - GET  /api/units/preferences, GET /api/units/groups, PATCH /api/units/preferences

All 152+ existing tests must continue to pass alongside these new tests.
"""

from __future__ import annotations

import sys
import threading
import time
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# ── Imports under test ────────────────────────────────────────────────────────
from supersonic_atomizer.gui.job_store import JobRecord, JobStore, get_job_store
from supersonic_atomizer.gui.plot_utils import figure_to_base64, figure_to_data_url
from supersonic_atomizer.gui.schemas import (
    CaseCreateRequest,
    JobStatusResponse,
    RunRequest,
    UnitUpdate,
)
from supersonic_atomizer.gui.session_store import SessionStore, get_session_store
from supersonic_atomizer.gui.state import GUIState


# ============================================================================
# 1. JobStore unit tests
# ============================================================================

class TestJobStore:

    def test_create_job_returns_uuid_string(self):
        store = JobStore()
        job_id = store.create_job()
        assert isinstance(job_id, str)
        uuid.UUID(job_id)  # must be valid UUID

    def test_initial_status_is_running(self):
        store = JobStore()
        job_id = store.create_job()
        record = store.get(job_id)
        assert record is not None
        assert record.status == "running"
        assert record.result is None
        assert record.error is None

    def test_mark_complete_sets_result(self):
        store = JobStore()
        job_id = store.create_job()
        mock_result = MagicMock()
        store.mark_complete(job_id, mock_result)
        record = store.get(job_id)
        assert record.status == "completed"
        assert record.result is mock_result

    def test_mark_failed_sets_error(self):
        store = JobStore()
        job_id = store.create_job()
        store.mark_failed(job_id, "some error")
        record = store.get(job_id)
        assert record.status == "failed"
        assert record.error == "some error"

    def test_get_unknown_id_returns_none(self):
        store = JobStore()
        assert store.get("nonexistent-id") is None

    def test_all_ids(self):
        store = JobStore()
        ids = [store.create_job() for _ in range(3)]
        for job_id in ids:
            assert job_id in store.all_ids()

    def test_thread_safety_concurrent_creates(self):
        store = JobStore()
        results = []
        errors = []

        def create_job():
            try:
                results.append(store.create_job())
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=create_job) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len(results) == 20
        assert len(set(results)) == 20  # all unique

    def test_module_singleton_is_jobstore(self):
        singleton = get_job_store()
        assert isinstance(singleton, JobStore)
        assert get_job_store() is singleton  # same object


# ============================================================================
# 2. SessionStore unit tests
# ============================================================================

class TestSessionStore:

    def test_get_or_create_returns_gui_state(self):
        store = SessionStore()
        sid = "test-session-001"
        state = store.get_or_create(sid)
        assert isinstance(state, GUIState)

    def test_get_or_create_idempotent(self):
        store = SessionStore()
        sid = "test-session-002"
        s1 = store.get_or_create(sid)
        s2 = store.get_or_create(sid)
        assert s1 is s2

    def test_get_returns_none_for_unknown_session(self):
        store = SessionStore()
        assert store.get("does-not-exist") is None

    def test_get_returns_existing_state(self):
        store = SessionStore()
        sid = "test-session-003"
        state = store.get_or_create(sid)
        assert store.get(sid) is state

    def test_delete_removes_session(self):
        store = SessionStore()
        sid = "test-session-004"
        store.get_or_create(sid)
        store.delete(sid)
        assert store.get(sid) is None

    def test_delete_nonexistent_is_noop(self):
        store = SessionStore()
        store.delete("does-not-exist")  # must not raise

    def test_new_session_id_is_unique(self):
        ids = {SessionStore.new_session_id() for _ in range(50)}
        assert len(ids) == 50

    def test_module_singleton_is_session_store(self):
        singleton = get_session_store()
        assert isinstance(singleton, SessionStore)
        assert get_session_store() is singleton


# ============================================================================
# 3. plot_utils unit tests
# ============================================================================

class TestPlotUtils:

    @pytest.fixture()
    def simple_figure(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        yield fig
        plt.close(fig)

    def test_figure_to_base64_returns_non_empty_string(self, simple_figure):
        result = figure_to_base64(simple_figure)
        assert isinstance(result, str)
        assert len(result) > 100  # must contain actual PNG data

    def test_figure_to_base64_is_valid_base64(self, simple_figure):
        import base64
        result = figure_to_base64(simple_figure)
        decoded = base64.b64decode(result)
        # PNG header: \x89PNG
        assert decoded[:4] == b"\x89PNG"

    def test_figure_to_data_url_prefix(self, simple_figure):
        url = figure_to_data_url(simple_figure)
        assert url.startswith("data:image/png;base64,")


# ============================================================================
# 4. Pydantic schemas unit tests
# ============================================================================

class TestSchemas:

    def test_case_create_request(self):
        req = CaseCreateRequest(name="my_case")
        assert req.name == "my_case"

    def test_run_request_defaults(self):
        req = RunRequest(case_name="demo")
        assert req.case_name == "demo"
        assert req.config == {}

    def test_run_request_with_config(self):
        req = RunRequest(case_name="demo", config={"key": "val"})
        assert req.config == {"key": "val"}

    def test_job_status_response_running(self):
        resp = JobStatusResponse(status="running")
        assert resp.status == "running"
        assert resp.error is None

    def test_job_status_response_failed(self):
        resp = JobStatusResponse(status="failed", error="oops")
        assert resp.error == "oops"

    def test_unit_update_extra_allowed(self):
        u = UnitUpdate(**{"pressure": "kPa", "temperature": "°C"})
        assert u.model_extra["pressure"] == "kPa"


# ============================================================================
# 5. FastAPI application factory tests
# ============================================================================

class TestFastAPIAppFactory:

    def test_create_app_returns_fastapi_instance(self):
        from fastapi import FastAPI
        from supersonic_atomizer.gui.fastapi_app import create_app
        app = create_app()
        assert isinstance(app, FastAPI)

    def test_create_app_has_expected_routes(self):
        from supersonic_atomizer.gui.fastapi_app import create_app
        app = create_app()
        paths = {r.path for r in app.routes}
        assert "/" in paths
        assert "/api/cases/" in paths
        assert "/api/simulation/run" in paths
        assert "/api/units/preferences" in paths


# ============================================================================
# 6. HTTP endpoint tests (TestClient — synchronous)
# ============================================================================

@pytest.fixture(scope="module")
def app_with_tmp_store(tmp_path_factory):
    """Return (app, tmp_cases_dir) with CaseStore backed by a temp directory."""
    from supersonic_atomizer.gui.case_store import CaseStore
    from supersonic_atomizer.gui.fastapi_app import create_app

    tmp_dir = tmp_path_factory.mktemp("fastapi_cases")
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
    # Restore
    _cr._get_store = original_cr
    _sr.CaseStore = original_sr_cls


@pytest.fixture(scope="module")
def client(app_with_tmp_store):
    from fastapi.testclient import TestClient
    app, _ = app_with_tmp_store
    with TestClient(app, raise_server_exceptions=True) as tc:
        yield tc


class TestIndexEndpoint:

    def test_get_root_returns_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert b"Supersonic Atomizer" in resp.content


class TestCasesEndpoints:

    def test_list_cases_empty(self, client):
        resp = client.get("/api/cases/")
        assert resp.status_code == 200
        assert "cases" in resp.json()

    def test_create_case(self, client):
        resp = client.post("/api/cases/", json={"name": "test_fastapi_case"})
        assert resp.status_code == 201
        assert resp.json()["name"] == "test_fastapi_case"

    def test_create_case_duplicate_returns_error(self, client):
        client.post("/api/cases/", json={"name": "dup_case_fa"})
        resp = client.post("/api/cases/", json={"name": "dup_case_fa"})
        # Should return 400 or similar error
        assert resp.status_code in (400, 409, 500)

    def test_get_case(self, client):
        client.post("/api/cases/", json={"name": "get_test_fa"})
        resp = client.get("/api/cases/get_test_fa")
        assert resp.status_code == 200
        data = resp.json()
        assert "fluid" in data

    def test_get_case_not_found(self, client):
        resp = client.get("/api/cases/does_not_exist_fa")
        assert resp.status_code == 404

    def test_put_case_updates_config(self, client):
        client.post("/api/cases/", json={"name": "put_test_fa"})
        existing = client.get("/api/cases/put_test_fa").json()
        existing["fluid"]["working_fluid"] = "steam"
        resp = client.put("/api/cases/put_test_fa", json=existing)
        assert resp.status_code == 200
        updated = client.get("/api/cases/put_test_fa").json()
        assert updated["fluid"]["working_fluid"] == "steam"

    def test_delete_case(self, client):
        client.post("/api/cases/", json={"name": "del_test_fa"})
        resp = client.delete("/api/cases/del_test_fa")
        assert resp.status_code == 204
        assert client.get("/api/cases/del_test_fa").status_code == 404


class TestSimulationEndpoints:
    """Tests for the simulation run/status/result flow (mocked solver)."""

    @pytest.fixture()
    def mock_bridge_run(self, monkeypatch):
        """Patch ServiceBridge to return a canned SimulationRunResult."""
        from supersonic_atomizer.app.services import SimulationRunResult
        mock_result = MagicMock(spec=SimulationRunResult)
        mock_result.status = "success"
        mock_result.simulation_result = None  # result endpoint will return 409

        monkeypatch.setattr(
            "supersonic_atomizer.gui.routers.simulation_router._bridge",
            MagicMock(run_simulation_sync=MagicMock(return_value=mock_result)),
        )
        return mock_result

    def test_status_unknown_job_returns_404(self, client):
        resp = client.get("/api/simulation/status/unknown-job-id")
        assert resp.status_code == 404

    def test_result_unknown_job_returns_404(self, client):
        resp = client.get("/api/simulation/result/unknown-job-id")
        assert resp.status_code == 404

    def test_run_nonexistent_case_returns_404(self, client):
        resp = client.post(
            "/api/simulation/run",
            json={"case_name": "absolutely_not_there"},
        )
        assert resp.status_code == 404

    def test_run_returns_job_id(self, client, mock_bridge_run):
        # Create a minimal case so exists() returns True
        client.post("/api/cases/", json={"name": "sim_run_test_fa"})
        resp = client.post(
            "/api/simulation/run",
            json={"case_name": "sim_run_test_fa"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        uuid.UUID(data["job_id"])  # must be a valid UUID

    def test_status_after_run_returns_valid_status(self, client, mock_bridge_run):
        client.post("/api/cases/", json={"name": "sim_status_test_fa"})
        run_resp = client.post(
            "/api/simulation/run",
            json={"case_name": "sim_status_test_fa"},
        )
        job_id = run_resp.json()["job_id"]
        # Poll until not running (allow up to 2 s for background thread)
        for _ in range(20):
            status_resp = client.get(f"/api/simulation/status/{job_id}")
            assert status_resp.status_code == 200
            if status_resp.json()["status"] != "running":
                break
            time.sleep(0.1)
        assert status_resp.json()["status"] in ("completed", "failed")


class TestUnitsEndpoints:

    def test_get_unit_groups(self, client):
        resp = client.get("/api/units/groups")
        assert resp.status_code == 200
        data = resp.json()
        # Must contain at least pressure group
        assert "pressure" in data
        assert isinstance(data["pressure"], list)
        assert len(data["pressure"]) >= 1

    def test_get_unit_preferences_returns_dict(self, client):
        resp = client.get("/api/units/preferences")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)

    def test_patch_unit_preferences(self, client):
        resp = client.patch(
            "/api/units/preferences",
            json={"pressure": "kPa"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("pressure") == "kPa"
