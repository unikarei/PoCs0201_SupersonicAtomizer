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
from dotenv import load_dotenv
import os
from urllib import request as _urlrequest, error as _urlerror
import json as _json
import logging as _logging

_GUI_DIR = Path(__file__).parent


def create_app() -> FastAPI:
    """Create and return the configured FastAPI application.

    This factory is used both at runtime (by uvicorn via the module-level
    ``app`` attribute) and in tests (via ``TestClient(create_app())``).
    """
    from supersonic_atomizer.gui.case_store import CaseStore
    from supersonic_atomizer.gui.output_artifact_store import sync_output_tree_with_cases
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

    # Startup output-tree reconciliation:
    # mirror cases/<project>/<case>.yaml into outputs/<project>/<case>/ and
    # move unmatched output folders under outputs/backup/.
    try:
        sync_output_tree_with_cases(CaseStore())
    except Exception as exc:  # pragma: no cover - non-fatal startup safety
        _logging.getLogger("supersonic_atomizer").warning(
            "Output tree synchronization failed at startup: %s", exc
        )

    return application


# Module-level singleton consumed by uvicorn:
#   uv run uvicorn supersonic_atomizer.gui.fastapi_app:app --reload
try:
    # Prefer a project-root .env file for local development. This does not
    # overwrite existing environment variables so system/user-level values
    # remain authoritative.
    project_root = Path(__file__).resolve().parents[3]
    dotenv_path = project_root / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path=str(dotenv_path), override=True)
    # Optional: validate OPENAI_API_KEY by querying the provider models endpoint.
    # Controlled by OPENAI_VALIDATE_ON_START env var (set to '1' or 'true' to enable).
    try:
        validate_on_start = str(os.environ.get("OPENAI_VALIDATE_ON_START", "1")).lower() in ("1", "true", "yes")
    except Exception:
        validate_on_start = True
    if validate_on_start:
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if api_key:
            try:
                _logging.getLogger("supersonic_atomizer").info("Validating OPENAI_API_KEY with provider...")
                base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
                req = _urlrequest.Request(
                    url=f"{base_url}/models",
                    method="GET",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                with _urlrequest.urlopen(req, timeout=6) as resp:
                    # If we get a usable JSON body, consider the key valid.
                    try:
                        _json.load(resp)
                        _logging.getLogger("supersonic_atomizer").info("OPENAI_API_KEY appears valid.")
                    except Exception:
                        _logging.getLogger("supersonic_atomizer").info("OPENAI_API_KEY validated (no parse error).")
            except _urlerror.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else str(exc)
                if exc.code == 401:
                    _logging.getLogger("supersonic_atomizer").warning(
                        "OPENAI API key appears invalid (HTTP 401). Chat features will return an error. "
                        "Check OPENAI_API_KEY or create a project .env from .env.example."
                    )
                else:
                    _logging.getLogger("supersonic_atomizer").warning(
                        f"OPENAI API key validation failed with HTTP {exc.code}: {detail[:200]}"
                    )
            except Exception as exc:  # network/timeout/etc
                _logging.getLogger("supersonic_atomizer").warning(
                    f"Could not validate OPENAI_API_KEY at startup: {exc}. Proceeding without blocking."
                )
except Exception:
    # Don't prevent the app from starting if dotenv is unavailable.
    pass

app = create_app()
