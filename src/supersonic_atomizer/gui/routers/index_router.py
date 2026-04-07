"""Index router — serves the main HTML page (P25-T04).

``GET /`` renders ``templates/index.html`` via Jinja2.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from supersonic_atomizer.gui.dependencies import get_or_create_session_id

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, response: Response) -> HTMLResponse:
    """Serve the main single-page application shell."""
    # Ensure a session cookie exists before the page loads.
    get_or_create_session_id(response)
    return _templates.TemplateResponse(request=request, name="index.html")
