"""Output artifact helpers for GUI startup synchronization and disk-backed restore.

This module intentionally stays in the GUI layer:
- It manages GUI runtime output layout conventions under outputs/<project>/<case>/run-*/.
- It does not run physics or mutate solver internals.
"""

from __future__ import annotations

import base64
import csv
import io
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt

from supersonic_atomizer.gui.case_store import CaseStore

matplotlib.use("Agg")

_OUTPUT_ROOT = Path("outputs")
_BACKUP_DIR_NAME = "backup"
_PREFERRED_PLOT_FIELD_ORDER: tuple[str, ...] = (
    "area_profile",
    "pressure",
    "temperature",
    "working_fluid_velocity",
    "droplet_velocity",
    "slip_velocity",
    "Mach_number",
    "mach_number",
    "droplet_mean_diameter",
    "droplet_maximum_diameter",
    "Weber_number",
    "weber_number",
    "pressure_over_total",
)


@dataclass(frozen=True, slots=True)
class OutputTreeSyncSummary:
    ensured_case_dirs: int
    moved_entries: int


def _safe_move(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    candidate = dst
    idx = 1
    while candidate.exists():
        candidate = dst.with_name(f"{dst.name}_{idx}")
        idx += 1
    shutil.move(str(src), str(candidate))


def sync_output_tree_with_cases(case_store: CaseStore, output_root: Path = _OUTPUT_ROOT) -> OutputTreeSyncSummary:
    """Mirror the cases tree under output root and move unmatched folders to backup.

    Rules:
    - Ensure outputs/<project>/<case>/ exists for every known case.
    - Any output entry not matching cases tree is moved under outputs/backup/.
    """

    output_root.mkdir(parents=True, exist_ok=True)
    backup_root = output_root / _BACKUP_DIR_NAME
    backup_root.mkdir(parents=True, exist_ok=True)

    project_to_cases: dict[str, set[str]] = {}
    for project in case_store.list_projects():
        project_to_cases[project] = set(case_store.list_cases(project=project))

    ensured = 0
    for project, cases in project_to_cases.items():
        for case_name in cases:
            (output_root / project / case_name).mkdir(parents=True, exist_ok=True)
            ensured += 1

    moved = 0
    for project_dir in output_root.iterdir():
        if project_dir.name == _BACKUP_DIR_NAME:
            continue
        if not project_dir.is_dir():
            _safe_move(project_dir, backup_root / "_unmatched_root" / project_dir.name)
            moved += 1
            continue

        project_name = project_dir.name
        expected_cases = project_to_cases.get(project_name)
        if expected_cases is None:
            _safe_move(project_dir, backup_root / "_unmatched_projects" / project_name)
            moved += 1
            continue

        for case_dir in list(project_dir.iterdir()):
            if not case_dir.is_dir():
                _safe_move(case_dir, backup_root / project_name / "_misc" / case_dir.name)
                moved += 1
                continue
            if case_dir.name not in expected_cases:
                _safe_move(case_dir, backup_root / project_name / case_dir.name)
                moved += 1

    return OutputTreeSyncSummary(ensured_case_dirs=ensured, moved_entries=moved)


def _pick_latest_run_dir(case_output_dir: Path) -> Path | None:
    if not case_output_dir.is_dir():
        return None
    run_dirs = [
        d
        for d in case_output_dir.iterdir()
        if d.is_dir() and (
            (d / "results.csv").is_file()
            or (d / "results.json").is_file()
            or (d / "plots").is_dir()
        )
    ]
    if not run_dirs:
        return None
    run_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    return run_dirs[0]


def has_case_output(project_name: str, case_name: str, output_root: Path = _OUTPUT_ROOT) -> bool:
    """Return True if at least one run artifact directory exists for the case."""

    case_dir = output_root / project_name / case_name
    return _pick_latest_run_dir(case_dir) is not None


def _parse_csv_rows(csv_text: str) -> list[dict[str, Any]]:
    lines = [line for line in csv_text.splitlines() if line and not line.startswith("#")]
    if not lines:
        return []

    reader = csv.DictReader(io.StringIO("\n".join(lines)))
    rows: list[dict[str, Any]] = []
    for row in reader:
        parsed: dict[str, Any] = {}
        for key, raw in row.items():
            value = (raw or "").strip()
            if value.lower() in {"true", "false"}:
                parsed[key] = value.lower() == "true"
                continue
            try:
                parsed[key] = float(value)
            except ValueError:
                parsed[key] = value
        rows.append(parsed)
    return rows


def _figure_to_base64(fig: Any) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _order_plot_fields(fields: list[str]) -> list[str]:
    index = {name: idx for idx, name in enumerate(_PREFERRED_PLOT_FIELD_ORDER)}
    return sorted(fields, key=lambda f: (index.get(f, len(index)), f))


def _build_plots_from_rows(rows: list[dict[str, Any]]) -> dict[str, str]:
    if not rows:
        return {}
    x_vals = [float(r.get("x", 0.0)) for r in rows]
    if not x_vals:
        return {}

    csv_to_plot_key = {
        "A": "area_profile",
        "pressure": "pressure",
        "temperature": "temperature",
        "working_fluid_velocity": "working_fluid_velocity",
        "droplet_velocity": "droplet_velocity",
        "slip_velocity": "slip_velocity",
        "Mach_number": "Mach_number",
        "droplet_mean_diameter": "droplet_mean_diameter",
        "droplet_maximum_diameter": "droplet_maximum_diameter",
        "Weber_number": "Weber_number",
    }

    plots: dict[str, str] = {}
    for csv_col, plot_key in csv_to_plot_key.items():
        if csv_col not in rows[0]:
            continue
        try:
            y_vals = [float(r.get(csv_col, 0.0)) for r in rows]
        except (TypeError, ValueError):
            continue
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(x_vals, y_vals)
        ax.set_xlabel("x [m]")
        ax.set_ylabel(csv_col)
        ax.set_title(plot_key.replace("_", " "))
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        plots[plot_key] = _figure_to_base64(fig)
        plt.close(fig)
    return plots


def load_last_result_payload_from_output(
    project_name: str,
    case_name: str,
    output_root: Path = _OUTPUT_ROOT,
) -> dict[str, Any] | None:
    """Load a last_result-like payload directly from output artifacts on disk."""

    case_dir = output_root / project_name / case_name
    run_dir = _pick_latest_run_dir(case_dir)
    if run_dir is None:
        return None

    csv_path = run_dir / "results.csv"
    csv_text = csv_path.read_text(encoding="utf-8") if csv_path.is_file() else ""
    table_rows = _parse_csv_rows(csv_text)

    plots: dict[str, str] = {}
    plots_dir = run_dir / "plots"
    if plots_dir.is_dir():
        for png in plots_dir.glob("*.png"):
            key = png.stem
            plots[key] = base64.b64encode(png.read_bytes()).decode("ascii")

    if not plots:
        plots = _build_plots_from_rows(table_rows)

    plot_fields = _order_plot_fields(list(plots.keys()))

    return {
        "status": "completed",
        "plots": plots,
        "plot_fields": plot_fields,
        "table_rows": table_rows,
        "csv": csv_text,
        "run_count": 1,
    }
