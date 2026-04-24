"""Simulation REST router — run / status / result endpoints (P25-T04).

Endpoints
---------
POST /api/simulation/run
    Accept a case name, resolve its YAML path, start a background solver
    thread, store the job in ``JobStore``, and return ``{"job_id": "..."}``.

GET  /api/simulation/status/{job_id}
    Return ``{"status": "running"|"completed"|"failed", "error": null|"..."}``.

GET  /api/simulation/result/{job_id}
    Return JSON with base64 plot images, table rows, and CSV content.

Non-blocking design (architecture.md B.7.2):
    The solver runs in a ``threading.Thread`` started by the ``/run``
    endpoint.  The browser polls ``/status/{job_id}`` every 800 ms until
    completion, then fetches ``/result/{job_id}`` once.
"""

from __future__ import annotations

import threading
from typing import Any

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")  # headless backend — safe for server context

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from supersonic_atomizer.gui.case_store import CaseNameError, CaseNotFoundError, CaseStore
from supersonic_atomizer.gui.dependencies import get_gui_state
from supersonic_atomizer.gui.job_store import get_job_store
from supersonic_atomizer.gui.multi_run import MultiRunSimulationResult, execute_expanded_runs, expand_multi_value_config
from supersonic_atomizer.gui.pages.post_graphs import PLOT_FIELDS, extract_overlay_plot_series, extract_plot_series
from supersonic_atomizer.gui.pages.post_table import aggregate_result_to_table_rows, generate_csv_content, result_to_table_rows
from supersonic_atomizer.gui.plot_utils import figure_to_base64
from supersonic_atomizer.gui.schemas import JobStatusResponse, RunRequest
from supersonic_atomizer.gui.service_bridge import ServiceBridge
from supersonic_atomizer.gui.state import GUIState

router = APIRouter()

# One shared bridge — thread-safe because ApplicationService is stateless per run.
_bridge = ServiceBridge()


def _run_job(job_id: str, case_path: str, gui_state: GUIState) -> None:
    """Background thread target — calls the solver and stores the result."""
    job_store = get_job_store()
    try:
        result = _bridge.run_simulation_sync(case_path)
        gui_state.last_run_result = result
        job_store.mark_complete(job_id, result)
    except Exception as exc:  # noqa: BLE001
        job_store.mark_failed(job_id, str(exc))


def _run_multi_job(
    job_id: str,
    case_name: str,
    config_snapshot: dict[str, Any],
    gui_state: GUIState,
) -> None:
    """Background thread target for multi-value Conditions sweeps."""
    job_store = get_job_store()
    try:
        expanded_runs = expand_multi_value_config(case_name=case_name, raw_config=config_snapshot)
        batch_result = execute_expanded_runs(
            case_name=case_name,
            expanded_runs=expanded_runs,
            runner=_bridge.run_simulation_sync,
        )
        if batch_result.runs:
            gui_state.last_run_result = batch_result.runs[-1].run_result
        job_store.mark_complete(job_id, batch_result)
    except Exception as exc:  # noqa: BLE001
        job_store.mark_failed(job_id, str(exc))


@router.post("/run")
async def run_simulation(
    body: RunRequest,
    gui_state: GUIState = Depends(get_gui_state),
) -> dict[str, str]:
    """Start a simulation run in the background and return a job identifier."""
    store = CaseStore()
    try:
        if not store.exists(body.case_name):
            raise HTTPException(
                status_code=404,
                detail=f"Case {body.case_name!r} not found.",
            )
        case_path = str(store.case_path(body.case_name))
    except CaseNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if body.config:
        try:
            expand_multi_value_config(case_name=body.case_name, raw_config=body.config)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    job_id = get_job_store().create_job()
    if body.config:
        thread = threading.Thread(
            target=_run_multi_job,
            args=(job_id, body.case_name, body.config, gui_state),
            daemon=True,
            name=f"solver-batch-{job_id[:8]}",
        )
    else:
        thread = threading.Thread(
            target=_run_job,
            args=(job_id, case_path, gui_state),
            daemon=True,
            name=f"solver-{job_id[:8]}",
        )
    thread.start()
    return {"job_id": job_id}


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_simulation_status(job_id: str) -> JobStatusResponse:
    """Return the current status of a simulation job."""
    record = get_job_store().get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found.")
    return JobStatusResponse(status=record.status, error=record.error)


@router.get("/result/{job_id}")
async def get_simulation_result(
    job_id: str,
    gui_state: GUIState = Depends(get_gui_state),
) -> JSONResponse:
    """Return plots (base64 PNG), table rows, and CSV for a completed job."""
    record = get_job_store().get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found.")
    if record.status != "completed" or record.result is None:
        raise HTTPException(status_code=409, detail="Job has not completed successfully.")

    prefs = gui_state.unit_preferences()

    plots: dict[str, str] = {}
    table_rows: list[dict[str, Any]]
    plot_fields: list[str]
    run_count = 1

    if isinstance(record.result, MultiRunSimulationResult):
        labeled_results = list(record.result.labeled_simulation_results())
        if not labeled_results:
            raise HTTPException(status_code=409, detail="Simulation result is not available.")
        overlay_series = extract_overlay_plot_series(labeled_results, prefs)
        for field, data in overlay_series.items():
            fig, ax = plt.subplots(figsize=(6.5, 3.5))
            for line in data["series"]:
                ax.plot(line["x"], line["y"], label=line["label"])
            ax.set_xlabel(data["x_label"])
            ax.set_ylabel(data["ylabel"])
            ax.set_title(data["title"])
            ax.grid(True, alpha=0.3)
            if len(data["series"]) > 1:
                ax.legend(fontsize="small")
            plt.tight_layout()
            plots[field] = figure_to_base64(fig)
            plt.close(fig)
        table_rows = aggregate_result_to_table_rows(labeled_results, prefs)
        plot_fields = list(overlay_series.keys())
        run_count = record.result.run_count
    else:
        run_result = record.result
        if run_result is None or run_result.simulation_result is None:
            raise HTTPException(status_code=409, detail="Simulation result is not available.")
        sim_result = run_result.simulation_result
        series = extract_plot_series(sim_result, prefs)
        for field, data in series.items():
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(data["x"], data["y"])
            ax.set_xlabel(data["x_label"])
            ax.set_ylabel(data["ylabel"])
            ax.set_title(data["title"])
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            plots[field] = figure_to_base64(fig)
            plt.close(fig)
        table_rows = result_to_table_rows(sim_result, prefs)
        plot_fields = list(series.keys())

    csv_content = generate_csv_content(table_rows)

    payload: dict[str, Any] = {
        "status": record.status,
        "plots": plots,
        "plot_fields": plot_fields,
        "table_rows": table_rows,
        "csv": csv_content,
        "run_count": run_count,
    }
    return JSONResponse(content=payload)
