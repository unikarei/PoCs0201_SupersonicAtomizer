from fastapi.testclient import TestClient
from supersonic_atomizer.gui.fastapi_app import create_app
from supersonic_atomizer.gui.case_store import CaseStore


def test_project_case_endpoint_returns_stored_yaml():
    app = create_app()
    client = TestClient(app)

    project = "001_Base"
    case = "TEST001-Air"

    # Load from CaseStore directly
    store = CaseStore()
    cfg = store.load(case, project=project)

    resp = client.get(f"/api/cases/projects/{project}/cases/{case}")
    assert resp.status_code == 200
    payload = resp.json()

    # Basic assertions that boundary conditions were loaded
    assert payload.get("boundary_conditions", {}).get("Pt_in") == cfg.get("boundary_conditions", {}).get("Pt_in")
    assert payload.get("boundary_conditions", {}).get("Tt_in") == cfg.get("boundary_conditions", {}).get("Tt_in")
    assert payload.get("boundary_conditions", {}).get("Ps_out") == cfg.get("boundary_conditions", {}).get("Ps_out")
