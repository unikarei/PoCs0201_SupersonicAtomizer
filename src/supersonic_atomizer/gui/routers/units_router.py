"""Units REST router — unit-preference CRUD (P25-T04).

Endpoints
---------
GET   /api/units/preferences          Return current unit preferences dict.
PATCH /api/units/preferences          Partial-update unit preferences.
GET   /api/units/groups               Return available unit groups/options.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from supersonic_atomizer.gui.dependencies import get_gui_state
from supersonic_atomizer.gui.pages.unit_settings_page import apply_unit_preference
from supersonic_atomizer.gui.state import GUIState
from supersonic_atomizer.gui.unit_settings import UNIT_GROUPS

router = APIRouter()


@router.get("/preferences")
async def get_unit_preferences(
    state: GUIState = Depends(get_gui_state),
) -> dict[str, str]:
    """Return the current per-group unit preferences."""
    return state.unit_preferences()


@router.patch("/preferences")
async def patch_unit_preferences(
    updates: dict[str, str],
    state: GUIState = Depends(get_gui_state),
) -> dict[str, str]:
    """Apply partial updates to unit preferences and return the full map."""
    for group, unit_label in updates.items():
        apply_unit_preference(state, group, unit_label)
    return state.unit_preferences()


@router.get("/groups")
async def get_unit_groups() -> dict[str, Any]:
    """Return all unit groups with conversion specs for each option.

    Returns a nested dict: ``{group: {label: {scale, offset}}}``.
    ``scale`` and ``offset`` satisfy: ``display = si * scale + offset``.
    """
    return {
        group: {
            label: {"scale": spec.scale, "offset": spec.offset}
            for label, spec in options.items()
        }
        for group, options in UNIT_GROUPS.items()
    }
