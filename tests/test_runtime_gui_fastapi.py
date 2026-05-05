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
    ChatReplyResponse,
    ChatRequest,
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

    def test_chat_request(self):
        req = ChatRequest(case_name="my_case", messages=[{"role": "user", "content": "status?"}])
        assert req.case_name == "my_case"
        assert req.messages[0].role == "user"

    def test_chat_reply_response(self):
        resp = ChatReplyResponse(reply={"role": "assistant", "content": "hello"})
        assert resp.reply.content == "hello"


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
        assert "/api/chat/messages" in paths
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
    import supersonic_atomizer.gui.routers.chat_router as _chr
    import supersonic_atomizer.gui.routers.simulation_router as _sr
    original_cr = _cr._get_store
    original_chr = _chr._get_store
    original_sr_cls = _sr.CaseStore
    _cr._get_store = _get_store_func
    _chr._get_store = _get_store_func
    _sr.CaseStore = lambda: store
    yield app, tmp_dir
    # Restore
    _cr._get_store = original_cr
    _chr._get_store = original_chr
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

    def test_get_root_contains_project_case_tree_markup(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        html = resp.text
        assert 'id="project-case-tree"' in html
        assert 'id="tree-context-menu"' in html
        assert 'id="left-panel-resize-handle"' in html
        assert 'id="right-panel-resize-handle"' in html
        assert 'id="chat-messages"' in html
        assert 'id="chat-form"' in html
        assert 'data-tab="post-report"' in html
        assert 'id="report-content"' in html
        assert "Right-click a project or case" in html

    def test_get_favicon_returns_no_content(self, client):
        resp = client.get("/favicon.ico")
        assert resp.status_code == 204


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

    def test_list_projects(self, client):
        resp = client.get("/api/cases/projects/")
        assert resp.status_code == 200
        data = resp.json()
        assert "projects" in data
        assert "default_project" in data

    def test_list_projects_materializes_legacy_default_cases(self, client, app_with_tmp_store):
        _, tmp_dir = app_with_tmp_store
        legacy_case = tmp_dir / "legacy_case.yaml"
        legacy_case.write_text("fluid:\n  working_fluid: air\n", encoding="utf-8")
        resp = client.get("/api/cases/projects/")
        assert resp.status_code == 200
        assert not legacy_case.exists()
        assert (tmp_dir / "default" / "legacy_case.yaml").exists()

    def test_create_project(self, client):
        resp = client.post("/api/cases/projects/", json={"name": "proj_fastapi"})
        assert resp.status_code == 201
        assert resp.json()["name"] == "proj_fastapi"

    def test_delete_project(self, client):
        client.post("/api/cases/projects/", json={"name": "proj_delete"})
        resp = client.delete("/api/cases/projects/proj_delete")
        assert resp.status_code == 204

    def test_rename_project(self, client):
        client.post("/api/cases/projects/", json={"name": "proj_old"})
        resp = client.post("/api/cases/projects/proj_old/rename", json={"new_name": "proj_new"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "proj_new"

    def test_export_project(self, client):
        client.post("/api/cases/projects/", json={"name": "proj_zip"})
        client.post("/api/cases/projects/proj_zip/cases/", json={"name": "case_a"})
        resp = client.get("/api/cases/projects/proj_zip/export")
        assert resp.status_code == 200
        assert "application/zip" in resp.headers["content-type"]
        assert resp.content.startswith(b"PK")

    def test_create_and_get_project_case(self, client):
        client.post("/api/cases/projects/", json={"name": "proj_fastapi"})
        create_resp = client.post("/api/cases/projects/proj_fastapi/cases/", json={"name": "case_in_project"})
        assert create_resp.status_code == 201
        get_resp = client.get("/api/cases/projects/proj_fastapi/cases/case_in_project")
        assert get_resp.status_code == 200
        assert "fluid" in get_resp.json()

    def test_list_project_cases(self, client):
        client.post("/api/cases/projects/", json={"name": "proj_fastapi"})
        client.post("/api/cases/projects/proj_fastapi/cases/", json={"name": "case_a"})
        resp = client.get("/api/cases/projects/proj_fastapi/cases/")
        assert resp.status_code == 200
        assert "case_a" in resp.json()["cases"]

    def test_duplicate_project_case(self, client):
        client.post("/api/cases/projects/", json={"name": "proj_duplicate"})
        client.post("/api/cases/projects/proj_duplicate/cases/", json={"name": "case_a"})
        resp = client.post(
            "/api/cases/projects/proj_duplicate/cases/case_a/duplicate",
            json={"new_name": "case_b"},
        )
        assert resp.status_code == 201
        listed = client.get("/api/cases/projects/proj_duplicate/cases/").json()["cases"]
        assert "case_b" in listed

    def test_rename_project_case(self, client):
        client.post("/api/cases/projects/", json={"name": "proj_rename_case"})
        client.post("/api/cases/projects/proj_rename_case/cases/", json={"name": "case_a"})
        resp = client.post(
            "/api/cases/projects/proj_rename_case/cases/case_a/rename",
            json={"new_name": "case_b"},
        )
        assert resp.status_code == 200
        listed = client.get("/api/cases/projects/proj_rename_case/cases/").json()["cases"]
        assert "case_b" in listed

    def test_move_project_case_between_projects(self, client):
        client.post("/api/cases/projects/", json={"name": "proj_source"})
        client.post("/api/cases/projects/", json={"name": "proj_target"})
        client.post("/api/cases/projects/proj_source/cases/", json={"name": "case_a"})
        resp = client.post(
            "/api/cases/projects/proj_source/cases/case_a/rename",
            json={"new_name": "case_a", "target_project": "proj_target"},
        )
        assert resp.status_code == 200
        source_cases = client.get("/api/cases/projects/proj_source/cases/").json()["cases"]
        target_cases = client.get("/api/cases/projects/proj_target/cases/").json()["cases"]
        assert "case_a" not in source_cases
        assert "case_a" in target_cases

    def test_export_project_case(self, client):
        client.post("/api/cases/projects/", json={"name": "proj_export"})
        client.post("/api/cases/projects/proj_export/cases/", json={"name": "case_a"})
        resp = client.get("/api/cases/projects/proj_export/cases/case_a/export")
        assert resp.status_code == 200
        assert "application/x-yaml" in resp.headers["content-type"]
        assert "fluid:" in resp.text

    def test_startup_output_sync_creates_case_dirs_and_moves_unmatched(self, tmp_path):
        from supersonic_atomizer.gui.case_store import CaseStore
        from supersonic_atomizer.gui.output_artifact_store import sync_output_tree_with_cases

        cases_dir = tmp_path / "cases"
        outputs_dir = tmp_path / "outputs"
        store = CaseStore(cases_dir=cases_dir)
        store.create_project("P1")
        store.create("C1", project="P1")
        store.create("C2", project="P1")

        # unmatched output entries that should be moved to backup
        (outputs_dir / "OrphanProject" / "OrphanCase").mkdir(parents=True, exist_ok=True)
        (outputs_dir / "random_file.txt").write_text("x", encoding="utf-8")

        summary = sync_output_tree_with_cases(store, output_root=outputs_dir)

        assert (outputs_dir / "P1" / "C1").is_dir()
        assert (outputs_dir / "P1" / "C2").is_dir()
        assert summary.ensured_case_dirs == 2
        assert summary.moved_entries >= 2
        assert not (outputs_dir / "OrphanProject").exists()
        assert (outputs_dir / "backup").is_dir()

    def test_project_case_has_result_true_from_disk_artifacts(self, client, app_with_tmp_store):
        _, tmp_dir = app_with_tmp_store
        # Create project/case in CaseStore used by the app.
        client.post("/api/cases/projects/", json={"name": "disk_proj"})
        client.post("/api/cases/projects/disk_proj/cases/", json={"name": "disk_case"})

        # Emulate existing output artifacts on disk after restart.
        run_dir = Path("outputs") / "disk_proj" / "disk_case" / "run-20260101T000000Z"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "results.csv").write_text(
            "# UNITS: {}\n"
            "x,A,pressure,temperature,density,working_fluid_velocity,Mach_number,droplet_velocity,slip_velocity,droplet_mean_diameter,droplet_maximum_diameter,Weber_number,breakup_flag,droplet_reynolds_number\n"
            "0.0,1e-4,200000,500,1.2,120,0.8,10,5,5e-5,1e-4,8,false,200\n",
            encoding="utf-8",
        )

        try:
            resp = client.get("/api/cases/projects/disk_proj/cases/disk_case")
            assert resp.status_code == 200
            assert resp.json().get("has_result") is True
        finally:
            # cleanup local artifacts created by this test
            import shutil
            shutil.rmtree(Path("outputs") / "disk_proj", ignore_errors=True)

    def test_project_case_last_result_falls_back_to_disk(self, client):
        client.post("/api/cases/projects/", json={"name": "disk_proj2"})
        client.post("/api/cases/projects/disk_proj2/cases/", json={"name": "disk_case2"})

        run_dir = Path("outputs") / "disk_proj2" / "disk_case2" / "run-20260101T010101Z"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "results.csv").write_text(
            "# UNITS: {}\n"
            "x,A,pressure,temperature,density,working_fluid_velocity,Mach_number,droplet_velocity,slip_velocity,droplet_mean_diameter,droplet_maximum_diameter,Weber_number,breakup_flag,droplet_reynolds_number\n"
            "0.0,1e-4,210000,510,1.1,130,0.9,11,4,4e-5,8e-5,9,false,210\n",
            encoding="utf-8",
        )

        try:
            resp = client.get("/api/cases/projects/disk_proj2/cases/disk_case2/last_result")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "completed"
            assert isinstance(data.get("table_rows"), list)
            assert len(data["table_rows"]) == 1
            assert "csv" in data and "pressure" in data["csv"]
        finally:
            import shutil
            shutil.rmtree(Path("outputs") / "disk_proj2", ignore_errors=True)


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

    def test_run_project_case_returns_job_id(self, client, mock_bridge_run):
        client.post("/api/cases/projects/", json={"name": "proj_sim"})
        client.post("/api/cases/projects/proj_sim/cases/", json={"name": "sim_case"})
        resp = client.post(
            "/api/simulation/run",
            json={"project_name": "proj_sim", "case_name": "sim_case"},
        )
        assert resp.status_code == 200
        uuid.UUID(resp.json()["job_id"])


class TestChatEndpoints:

    def test_send_chat_message_returns_reply(self, client, monkeypatch, tmp_path):
        from supersonic_atomizer.gui.routers import chat_router
        from supersonic_atomizer.gui.chat_history_store import ChatHistoryStore

        history_store = ChatHistoryStore(root_dir=tmp_path / "chat_histories_reply")
        monkeypatch.setattr(chat_router, "_chat_history_store", history_store)

        client.post("/api/cases/projects/", json={"name": "chat_proj"})
        client.post("/api/cases/projects/chat_proj/cases/", json={"name": "chat_case"})

        mock_service = MagicMock()
        mock_service.generate_reply.return_value = "Case looks stable."
        monkeypatch.setattr(chat_router, "_chat_service", mock_service)

        resp = client.post(
            "/api/chat/messages",
            json={
                "project_name": "chat_proj",
                "case_name": "chat_case",
                "messages": [{"role": "user", "content": "Summarize this case."}],
            },
        )

        assert resp.status_code == 200
        assert resp.json()["reply"] == {"role": "assistant", "content": "Case looks stable."}
        assert resp.json().get("thread_id")
        mock_service.generate_reply.assert_called_once()

    def test_chat_threads_crud_and_persistence(self, client, monkeypatch, tmp_path):
        from supersonic_atomizer.gui.routers import chat_router
        from supersonic_atomizer.gui.chat_history_store import ChatHistoryStore

        history_store = ChatHistoryStore(root_dir=tmp_path / "chat_histories")
        monkeypatch.setattr(chat_router, "_chat_history_store", history_store)

        client.post("/api/cases/projects/", json={"name": "chat_proj_crud"})
        client.post("/api/cases/projects/chat_proj_crud/cases/", json={"name": "chat_case_crud"})

        create_resp = client.post(
            "/api/chat/threads",
            json={
                "project_name": "chat_proj_crud",
                "case_name": "chat_case_crud",
                "title": "Initial thread",
            },
        )
        assert create_resp.status_code == 201
        thread_id = create_resp.json()["id"]

        list_resp = client.get("/api/chat/threads", params={"project_name": "chat_proj_crud", "case_name": "chat_case_crud"})
        assert list_resp.status_code == 200
        assert any(t["id"] == thread_id for t in list_resp.json()["threads"])

        rename_resp = client.patch(
            f"/api/chat/threads/{thread_id}",
            json={
                "project_name": "chat_proj_crud",
                "case_name": "chat_case_crud",
                "title": "Renamed thread",
            },
        )
        assert rename_resp.status_code == 200
        assert rename_resp.json()["title"] == "Renamed thread"

        replace_resp = client.put(
            f"/api/chat/threads/{thread_id}/messages",
            json={
                "project_name": "chat_proj_crud",
                "case_name": "chat_case_crud",
                "messages": [
                    {"role": "user", "content": "hello"},
                    {"role": "assistant", "content": "world"},
                ],
            },
        )
        assert replace_resp.status_code == 200
        assert len(replace_resp.json()["messages"]) == 2

        delete_resp = client.delete(
            f"/api/chat/threads/{thread_id}",
            params={"project_name": "chat_proj_crud", "case_name": "chat_case_crud"},
        )
        assert delete_resp.status_code == 204

    def test_send_chat_message_missing_case_returns_404(self, client):
        resp = client.post(
            "/api/chat/messages",
            json={
                "case_name": "missing_case",
                "messages": [{"role": "user", "content": "hello"}],
            },
        )
        assert resp.status_code == 404

    def test_generate_summary_returns_text(self, client, monkeypatch, tmp_path):
        from supersonic_atomizer.gui.routers import chat_router
        from supersonic_atomizer.gui.chat_history_store import ChatHistoryStore

        history_store = ChatHistoryStore(root_dir=tmp_path / "chat_histories_summary")
        monkeypatch.setattr(chat_router, "_chat_history_store", history_store)

        client.post("/api/cases/projects/", json={"name": "sum_proj"})
        client.post("/api/cases/projects/sum_proj/cases/", json={"name": "sum_case"})

        # Create a thread and populate it with some messages.
        thread_resp = client.post(
            "/api/chat/threads",
            json={"project_name": "sum_proj", "case_name": "sum_case", "title": "Summary test"},
        )
        assert thread_resp.status_code == 201
        thread_id = thread_resp.json()["id"]

        client.put(
            f"/api/chat/threads/{thread_id}/messages",
            json={
                "project_name": "sum_proj",
                "case_name": "sum_case",
                "messages": [
                    {"role": "user", "content": "What is the Mach number at exit?"},
                    {"role": "assistant", "content": "The Mach number at exit is approximately 1.74."},
                ],
            },
        )

        mock_service = MagicMock()
        mock_service.generate_reply.return_value = "Exit Mach ~1.74, supersonic flow."
        monkeypatch.setattr(chat_router, "_chat_service", mock_service)

        resp = client.post(
            "/api/chat/summary",
            json={
                "project_name": "sum_proj",
                "case_name": "sum_case",
                "thread_id": thread_id,
                "max_chars": 300,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert isinstance(data["summary"], str)
        assert len(data["summary"]) > 0
        mock_service.generate_reply.assert_called_once()

    def test_generate_summary_with_refine_prompt(self, client, monkeypatch, tmp_path):
        from supersonic_atomizer.gui.routers import chat_router
        from supersonic_atomizer.gui.chat_history_store import ChatHistoryStore

        history_store = ChatHistoryStore(root_dir=tmp_path / "chat_histories_refine")
        monkeypatch.setattr(chat_router, "_chat_history_store", history_store)

        client.post("/api/cases/projects/", json={"name": "ref_proj"})
        client.post("/api/cases/projects/ref_proj/cases/", json={"name": "ref_case"})

        thread_resp = client.post(
            "/api/chat/threads",
            json={"project_name": "ref_proj", "case_name": "ref_case", "title": "Refine test"},
        )
        thread_id = thread_resp.json()["id"]
        client.put(
            f"/api/chat/threads/{thread_id}/messages",
            json={
                "project_name": "ref_proj",
                "case_name": "ref_case",
                "messages": [{"role": "user", "content": "Explain breakup."}, {"role": "assistant", "content": "Breakup occurs when We > 12."}],
            },
        )

        mock_service = MagicMock()
        mock_service.generate_reply.return_value = "Breakup when We exceeds critical value."
        monkeypatch.setattr(chat_router, "_chat_service", mock_service)

        resp = client.post(
            "/api/chat/summary",
            json={
                "project_name": "ref_proj",
                "case_name": "ref_case",
                "thread_id": thread_id,
                "max_chars": 150,
                "refine_prompt": "英語で短く",
            },
        )
        assert resp.status_code == 200
        assert isinstance(resp.json()["summary"], str)
        # Verify refine_prompt was forwarded in the messages sent to the service.
        call_kwargs = mock_service.generate_reply.call_args.kwargs
        last_msg_content = call_kwargs["messages"][-1]["content"]
        assert "英語で短く" in last_msg_content


class TestUnitsEndpoints:

    def test_get_unit_groups(self, client):
        resp = client.get("/api/units/groups")
        assert resp.status_code == 200
        data = resp.json()
        # Must contain at least pressure group with spec format {label: {scale, offset}}
        assert "pressure" in data
        assert isinstance(data["pressure"], dict)
        assert len(data["pressure"]) >= 1
        # Check that pressure group has at least "Pa" as a unit
        assert "Pa" in data["pressure"]
        # Check the spec has scale and offset
        pa_spec = data["pressure"]["Pa"]
        assert isinstance(pa_spec, dict)
        assert "scale" in pa_spec
        assert "offset" in pa_spec
        assert pa_spec["scale"] == 1.0

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
