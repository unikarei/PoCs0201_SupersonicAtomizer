"""Cases REST router — CRUD for simulation cases (P25-T04).

Endpoints
---------
GET    /api/cases/           List all case names.
POST   /api/cases/           Create a new (empty skeleton) case.
GET    /api/cases/{name}     Load and return a case config dict.
PUT    /api/cases/{name}     Save / overwrite a case config dict.
DELETE /api/cases/{name}     Delete a case.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, Response

from supersonic_atomizer.gui.dependencies import get_gui_state
from supersonic_atomizer.gui.state import GUIState

from supersonic_atomizer.gui.case_store import CaseNameError, CaseNotFoundError, CaseStore, ProjectNameError, ProjectNotFoundError
from supersonic_atomizer.gui.job_store import get_job_store
from supersonic_atomizer.gui.multi_run import MultiRunSimulationResult
from supersonic_atomizer.gui.pages.post_graphs import extract_overlay_plot_series, extract_plot_series
from supersonic_atomizer.gui.pages.post_table import aggregate_result_to_table_rows, generate_csv_content, result_to_table_rows
from supersonic_atomizer.gui.plot_utils import figure_to_base64
import base64
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")
from supersonic_atomizer.gui.schemas import CaseCreateRequest, CaseDuplicateRequest, CaseRenameRequest, ProjectCreateRequest, ProjectRenameRequest

router = APIRouter()

_SKELETON: dict[str, Any] = {
    "fluid": {"working_fluid": "air"},
    "boundary_conditions": {
        "Pt_in": 200_000.0,
        "Tt_in": 300.0,
        "Ps_out": 101_325.0,
    },
    "geometry": {
        "x_start": 0.0,
        "x_end": 0.5,
        "num_cells": 100,
        "area_table": [
            {"x": 0.0, "A": 0.01},
            {"x": 0.25, "A": 0.005},
            {"x": 0.5, "A": 0.01},
        ],
    },
    "droplet_injection": {
        "droplet_velocity_in": 10.0,
        "droplet_diameter_mean_in": 50e-6,
        "droplet_diameter_max_in": 100e-6,
    },
    "model_selection": {
        "breakup_model": "weber_critical",
        "critical_weber_number": 12.0,
        "breakup_factor_mean": 0.5,
        "breakup_factor_max": 0.5,
        "drag_model": "standard_sphere",
        "coupling_mode": "one_way",
    },
    "outputs": {
        "output_dir": "outputs",
        "write_csv": True,
        "write_json": True,
        "generate_plots": True,
    },
}


def _get_store() -> CaseStore:
    return CaseStore()


def _case_ref(project: str, name: str) -> str:
    return f"{project}/{name}"


def _materialize_default_project(store: CaseStore) -> None:
    """Move legacy root-level cases into cases/default/ for canonical GUI storage."""
    store.migrate_legacy_cases(target_project=store.default_project_name)


@router.get("/projects/")
async def list_projects() -> dict[str, Any]:
    """Return all saved project names and the default project name."""
    store = _get_store()
    _materialize_default_project(store)
    return {
        "projects": store.list_projects(),
        "default_project": store.default_project_name,
    }


@router.post("/projects/", status_code=201)
async def create_project(body: ProjectCreateRequest) -> dict[str, str]:
    """Create an empty project directory."""
    store = _get_store()
    try:
        store.create_project(body.name)
    except ProjectNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"name": body.name}


@router.delete("/projects/{project}", status_code=204)
async def delete_project(project: str) -> None:
    """Delete a project and all cases contained within it."""
    store = _get_store()
    try:
        store.delete_project(project)
    except ProjectNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/projects/{project}/rename")
async def rename_project(project: str, body: ProjectRenameRequest) -> dict[str, str]:
    """Rename a project and preserve its contained cases."""
    store = _get_store()
    try:
        path = store.rename_project(project, body.new_name)
    except ProjectNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"name": path.name}


@router.get("/projects/{project}/export")
async def export_project(project: str) -> Response:
    """Return a ZIP archive containing all YAML cases in the selected project."""
    store = _get_store()
    try:
        payload = store.export_project_archive(project)
    except ProjectNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(
        content=payload,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{project}.zip"',
        },
    )


@router.get("/projects/{project}/cases/")
async def list_project_cases(project: str) -> dict[str, Any]:
    """Return all case names for the selected project."""
    store = _get_store()
    try:
        return {"project": project, "cases": store.list_cases(project=project)}
    except ProjectNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/projects/{project}/cases/", status_code=201)
async def create_project_case(project: str, body: CaseCreateRequest) -> dict[str, str]:
    """Create an empty skeleton case in the selected project."""
    store = _get_store()
    try:
        store.create(body.name, _SKELETON, project=project)
    except (ProjectNameError, CaseNameError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"project": project, "name": body.name}


@router.get("/projects/{project}/cases/{name}")
async def get_project_case(project: str, name: str) -> dict[str, Any]:
    """Return the stored config dict for a project-scoped case."""
    store = _get_store()
    try:
        return store.load(name, project=project)
    except ProjectNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/projects/{project}/cases/{name}")
async def save_project_case(project: str, name: str, config: dict[str, Any]) -> dict[str, str]:
    """Overwrite the stored config for a project-scoped case."""
    store = _get_store()
    try:
        store.save(name, config, project=project)
    except ProjectNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"project": project, "name": name}


@router.delete("/projects/{project}/cases/{name}", status_code=204)
async def delete_project_case(project: str, name: str) -> None:
    """Delete the selected project-scoped case."""
    store = _get_store()
    try:
        store.delete(name, project=project)
    except ProjectNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/projects/{project}/cases/{name}/duplicate", status_code=201)
async def duplicate_project_case(project: str, name: str, body: CaseDuplicateRequest) -> dict[str, str]:
    """Duplicate the selected project case under a new case name."""
    store = _get_store()
    try:
        path = store.duplicate(
            name,
            body.new_name,
            project=project,
            target_project=body.target_project or project,
        )
    except (ProjectNameError, CaseNameError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "project": path.parent.name,
        "name": path.stem,
    }


@router.post("/projects/{project}/cases/{name}/rename")
async def rename_project_case(project: str, name: str, body: CaseRenameRequest) -> dict[str, str]:
    """Rename a project case, optionally moving it to another project."""
    store = _get_store()
    try:
        path = store.rename_case(
            name,
            body.new_name,
            project=project,
            target_project=body.target_project or project,
        )
    except (ProjectNameError, CaseNameError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "project": path.parent.name,
        "name": path.stem,
    }


@router.get("/projects/{project}/cases/{name}/export")
async def export_project_case(project: str, name: str) -> PlainTextResponse:
    """Return the selected project case as YAML text for download/export."""
    store = _get_store()
    try:
        payload = store.export_yaml(name, project=project)
    except ProjectNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PlainTextResponse(
        payload,
        media_type="application/x-yaml",
        headers={
            "Content-Disposition": f'attachment; filename="{project}-{name}.yaml"',
        },
    )


@router.get("/projects/{project}/cases/{name}/last_result")
async def get_last_result_for_project_case(project: str, name: str, state: GUIState = Depends(get_gui_state)) -> dict[str, Any]:
    """Return the most recent completed simulation result for a project case."""
    job_store = get_job_store()
    record = job_store.latest_completed_for_case(_case_ref(project, name))
    if record is None:
        raise HTTPException(status_code=404, detail=f"No completed run found for case {name!r} in project {project!r}.")

    plots: dict[str, str] = {}
    table_rows: list[dict[str, Any]] = []
    plot_fields: list[str] = []
    run_count = 1

    prefs = state.unit_preferences()

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
        # Prefer file-backed plot images if the run wrote artifacts to disk.
        metadata = sim_result.output_metadata
        if metadata and metadata.plot_paths:
            for field, path_str in metadata.plot_paths.items():
                p = Path(path_str)
                if p.is_file():
                    with p.open("rb") as fh:
                        plots[field] = base64.b64encode(fh.read()).decode("ascii")
                else:
                    # fallback to in-memory generation for missing files
                    data = extract_plot_series(sim_result, prefs).get(field)
                    if data is None:
                        continue
                    fig, ax = plt.subplots(figsize=(6, 3))
                    ax.plot(data["x"], data["y"])
                    ax.set_xlabel(data["x_label"])
                    ax.set_ylabel(data["ylabel"])
                    ax.set_title(data["title"])
                    ax.grid(True, alpha=0.3)
                    plt.tight_layout()
                    plots[field] = figure_to_base64(fig)
                    plt.close(fig)
        else:
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

    # Prefer reading CSV from disk when available
    csv_content = generate_csv_content(table_rows)
    try:
        if 'sim_result' in locals() and sim_result.output_metadata and sim_result.output_metadata.csv_path:
            csv_path = Path(sim_result.output_metadata.csv_path)
            if csv_path.is_file():
                csv_content = csv_path.read_text(encoding='utf-8')
    except Exception:
        # fallback to generated CSV on any error
        pass

    return {
        "status": record.status,
        "plots": plots,
        "plot_fields": plot_fields,
        "table_rows": table_rows,
        "csv": csv_content,
        "run_count": run_count,
    }


@router.get("/")
async def list_cases() -> dict[str, list[str]]:
    """Return all saved case names."""
    return {"cases": _get_store().list_cases()}


@router.post("/", status_code=201)
async def create_case(body: CaseCreateRequest) -> dict[str, str]:
    """Create an empty skeleton case with *body.name*."""
    store = _get_store()
    try:
        store.create(body.name, _SKELETON)
    except CaseNameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"name": body.name}


@router.get("/{name}")
async def get_case(name: str) -> dict[str, Any]:
    """Return the stored config dict for *name*."""
    store = _get_store()
    try:
        return store.load(name)
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{name}")
async def save_case(name: str, config: dict[str, Any]) -> dict[str, str]:
    """Overwrite the stored config for *name* with *config*."""
    store = _get_store()
    try:
        store.save(name, config)
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"name": name}


@router.delete("/{name}", status_code=204)
async def delete_case(name: str) -> None:
    """Delete the case identified by *name*."""
    store = _get_store()
    try:
        store.delete(name)
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.get("/{name}/last_result")
async def get_last_result_for_case(name: str, state: GUIState = Depends(get_gui_state)) -> dict[str, Any]:
    """Return the most recent completed simulation result payload for *name*.

    The payload mirrors ``/api/simulation/result/{job_id}`` and contains
    base64 plots, table rows, CSV text, and run_count when available. Uses
    default (SI) unit preferences to build figures.
    """
    job_store = get_job_store()
    record = job_store.latest_completed_for_case(name)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No completed run found for case {name!r}.")

    # Build payload similar to simulation_router.get_simulation_result
    plots: dict[str, str] = {}
    table_rows: list[dict[str, Any]] = []
    plot_fields: list[str] = []
    run_count = 1

    prefs = state.unit_preferences()

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

    return {
        "status": record.status,
        "plots": plots,
        "plot_fields": plot_fields,
        "table_rows": table_rows,
        "csv": csv_content,
        "run_count": run_count,
    }
