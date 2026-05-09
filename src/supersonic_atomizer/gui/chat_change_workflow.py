"""Chat-driven Conditions/Grid change proposal workflow.

Implements a proposal lifecycle so chat can suggest changes safely while
reusing the existing validation chain before persistence.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
import threading
from typing import Any
from uuid import uuid4

from supersonic_atomizer.config import (
    apply_config_defaults,
    translate_case_config,
    validate_raw_config_schema,
    validate_semantic_config,
)
from supersonic_atomizer.geometry import build_geometry_model
from supersonic_atomizer.thermo import select_thermo_provider

ALLOWED_PATH_PREFIXES = (
    "fluid.",
    "boundary_conditions.",
    "droplet_injection.",
    "models.",
    "geometry.",
)

TERMINAL_PROPOSAL_STATES = {"confirmed", "rejected"}


@dataclass
class ProposalRecord:
    proposal_id: str
    project_name: str | None
    case_name: str
    pattern: int
    reason: str | None
    status: str
    changes: list[dict[str, Any]]
    diff: list[dict[str, Any]]
    base_config: dict[str, Any]
    proposed_config: dict[str, Any]
    created_at: str
    updated_at: str


class ChatChangeWorkflowStore:
    """In-memory proposal lifecycle store for GUI chat config-change flows."""

    def __init__(self) -> None:
        self._records: dict[str, ProposalRecord] = {}
        self._lock = threading.Lock()

    def create(self, record: ProposalRecord) -> ProposalRecord:
        with self._lock:
            self._records[record.proposal_id] = record
        return record

    def get(self, proposal_id: str) -> ProposalRecord:
        with self._lock:
            try:
                return self._records[proposal_id]
            except KeyError as exc:
                raise KeyError(f"Unknown proposal_id: {proposal_id}") from exc

    def update_status(self, proposal_id: str, status: str) -> ProposalRecord:
        with self._lock:
            try:
                record = self._records[proposal_id]
            except KeyError as exc:
                raise KeyError(f"Unknown proposal_id: {proposal_id}") from exc
            record.status = status
            record.updated_at = _utcnow_iso()
            return record


def _utcnow_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _is_allowed_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in ALLOWED_PATH_PREFIXES)


def _set_nested_value(config: dict[str, Any], path: str, value: Any) -> None:
    keys = path.split(".")
    if any(not key for key in keys):
        raise ValueError(f"Invalid dotted path: {path!r}")

    target: Any = config
    for key in keys[:-1]:
        if not isinstance(target, dict):
            raise ValueError(f"Path segment {key!r} does not point to a mapping in path {path!r}.")
        if key not in target or target[key] is None:
            target[key] = {}
        if not isinstance(target[key], dict):
            raise ValueError(f"Path segment {key!r} is not a mapping in path {path!r}.")
        target = target[key]

    if not isinstance(target, dict):
        raise ValueError(f"Cannot set value for non-mapping target in path {path!r}.")
    target[keys[-1]] = value


def _get_nested_value(config: dict[str, Any], path: str) -> Any:
    keys = path.split(".")
    current: Any = config
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _validate_runtime_ready(config: dict[str, Any]) -> None:
    geometry_section = config.get("geometry")
    if isinstance(geometry_section, dict):
        if "n_cells" not in geometry_section and "num_cells" in geometry_section:
            geometry_section["n_cells"] = geometry_section["num_cells"]
        area_distribution = geometry_section.get("area_distribution")
        area_table = geometry_section.get("area_table")
        if not isinstance(area_distribution, dict) and isinstance(area_table, list):
            xs: list[float] = []
            areas: list[float] = []
            for row in area_table:
                if not isinstance(row, dict):
                    continue
                if "x" not in row or "A" not in row:
                    continue
                xs.append(row["x"])
                areas.append(row["A"])
            geometry_section["area_distribution"] = {
                "type": "table",
                "x": xs,
                "A": areas,
            }
    validate_raw_config_schema(config)
    validate_semantic_config(config)
    normalized = apply_config_defaults(config)
    case_config = translate_case_config(normalized)
    build_geometry_model(case_config.geometry)
    select_thermo_provider(case_config)


def apply_changes_with_validation(
    base_config: dict[str, Any],
    changes: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Apply Conditions/Grid-scoped changes and run existing validation chain."""

    if not changes:
        raise ValueError("At least one change is required.")

    candidate = deepcopy(base_config)
    diff_rows: list[dict[str, Any]] = []

    for entry in changes:
        path = str(entry.get("path", "")).strip()
        if not path:
            raise ValueError("Change path must be non-empty.")
        if not _is_allowed_path(path):
            raise ValueError(
                f"Path {path!r} is out of scope. Only Conditions/Grid paths are allowed."
            )
        new_value = entry.get("value")
        old_value = _get_nested_value(candidate, path)
        _set_nested_value(candidate, path, new_value)
        diff_rows.append({"path": path, "before": old_value, "after": new_value})

    _validate_runtime_ready(candidate)
    return candidate, diff_rows


def new_record(
    *,
    project_name: str | None,
    case_name: str,
    pattern: int,
    reason: str | None,
    changes: list[dict[str, Any]],
    base_config: dict[str, Any],
    proposed_config: dict[str, Any],
    diff: list[dict[str, Any]],
) -> ProposalRecord:
    now = _utcnow_iso()
    return ProposalRecord(
        proposal_id=str(uuid4()),
        project_name=project_name,
        case_name=case_name,
        pattern=pattern,
        reason=reason,
        status="proposed",
        changes=deepcopy(changes),
        diff=deepcopy(diff),
        base_config=deepcopy(base_config),
        proposed_config=deepcopy(proposed_config),
        created_at=now,
        updated_at=now,
    )
