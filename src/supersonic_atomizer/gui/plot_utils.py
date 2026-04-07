"""Matplotlib figure → base64 PNG helpers for FastAPI JSON responses (P25-T03).

The FastAPI simulation_router uses ``figure_to_base64`` to embed plot images
directly in JSON API responses so the browser can render them with a plain
``<img src="data:image/png;base64,...">`` tag — no static-file serving
required.
"""

from __future__ import annotations

import base64
import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import matplotlib.figure


def figure_to_base64(fig: "matplotlib.figure.Figure") -> str:
    """Serialize *fig* to a base64-encoded PNG string.

    Parameters
    ----------
    fig:
        A Matplotlib Figure instance.

    Returns
    -------
    str
        A base64-encoded PNG string suitable for embedding in a JSON payload
        or as the value of an HTML ``<img src="data:image/png;base64,...">``
        attribute.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=96)
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def figure_to_data_url(fig: "matplotlib.figure.Figure") -> str:
    """Return a complete ``data:`` URL for *fig* as a PNG.

    Convenience wrapper over :func:`figure_to_base64`.
    """
    return f"data:image/png;base64,{figure_to_base64(fig)}"
