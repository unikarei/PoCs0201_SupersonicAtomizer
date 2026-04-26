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

from fastapi import APIRouter, HTTPException

from supersonic_atomizer.gui.case_store import CaseNameError, CaseNotFoundError, CaseStore
from supersonic_atomizer.gui.schemas import CaseCreateRequest

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
