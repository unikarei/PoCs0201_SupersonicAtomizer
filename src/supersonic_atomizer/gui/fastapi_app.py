"""FastAPI application factory for the Supersonic Atomizer GUI (P25-T03).

Architectural boundary (architecture.md, Appendix B.7.2):
- This module is the FastAPI equivalent of the Streamlit gui/app.py.
- It assembles the FastAPI application, mounts routers and static files.
- All application service calls go through gui/routers/* via service_bridge.py.
- Solver, config, domain, IO, and plotting layers are not imported here.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

_GUI_DIR = Path(__file__).parent


def create_app() -> FastAPI:
    """Create and return the configured FastAPI application.

    This factory is used both at runtime (by uvicorn via the module-level
    ``app`` attribute) and in tests (via ``TestClient(create_app())``).
    """
    from supersonic_atomizer.gui.routers.cases_router import router as cases_r
    from supersonic_atomizer.gui.routers.chat_router import router as chat_r
    from supersonic_atomizer.gui.routers.index_router import router as index_r
    from supersonic_atomizer.gui.routers.simulation_router import router as sim_r
    from supersonic_atomizer.gui.routers.units_router import router as units_r
    from supersonic_atomizer.gui.routers.debug_router import router as debug_r

    application = FastAPI(
        title="Supersonic Atomizer GUI",
        description="FastAPI-based browser interface for the quasi-1D atomizer simulator.",
        version="0.1.0",
    )

    # Static files (CSS, JS)
    static_dir = _GUI_DIR / "static"
    static_dir.mkdir(exist_ok=True)
    application.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # API routers
    application.include_router(index_r)
    application.include_router(cases_r, prefix="/api/cases", tags=["cases"])
    application.include_router(chat_r, prefix="/api/chat", tags=["chat"])
    application.include_router(sim_r, prefix="/api/simulation", tags=["simulation"])
    application.include_router(units_r, prefix="/api/units", tags=["units"])
    application.include_router(debug_r, prefix="/api/debug", tags=["debug"])

    return application


# Module-level singleton consumed by uvicorn:
#   uv run uvicorn supersonic_atomizer.gui.fastapi_app:app --reload
app = create_app()
