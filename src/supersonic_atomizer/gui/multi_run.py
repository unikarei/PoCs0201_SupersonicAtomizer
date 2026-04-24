"""GUI-side multi-run helpers for Conditions(UI) parameter sweeps.

This module keeps multi-value numeric token parsing and solve-time sweep
expansion at the GUI/application orchestration boundary. Solver code continues
to receive one single-case YAML snapshot per run.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, Iterable
import re

import yaml

from supersonic_atomizer.app.services import SimulationRunResult
from supersonic_atomizer.domain import SimulationResult


MAX_SWEEP_RUNS = 32
_TOKEN_SPLIT_RE = re.compile(r"[,;\s，、]+")


@dataclass(frozen=True, slots=True)
class SweepFieldSpec:
    section_names: tuple[str, ...]
    field_name: str
    label: str
    optional: bool = False


@dataclass(frozen=True, slots=True)
class ExpandedRunConfig:
    run_index: int
    run_label: str
    config: dict[str, Any]


@dataclass(frozen=True, slots=True)
class LabeledSimulationRun:
    run_index: int
    run_label: str
    run_result: SimulationRunResult


@dataclass(frozen=True, slots=True)
class MultiRunSimulationResult:
    case_name: str
    runs: tuple[LabeledSimulationRun, ...]

    @property
    def run_count(self) -> int:
        return len(self.runs)

    def labeled_simulation_results(self) -> tuple[tuple[str, SimulationResult], ...]:
        labeled: list[tuple[str, SimulationResult]] = []
        for run in self.runs:
            if run.run_result.simulation_result is not None:
                labeled.append((run.run_label, run.run_result.simulation_result))
        return tuple(labeled)


SWEEP_FIELD_SPECS: tuple[SweepFieldSpec, ...] = (
    SweepFieldSpec(("boundary_conditions",), "Pt_in", "Pt_in"),
    SweepFieldSpec(("boundary_conditions",), "Tt_in", "Tt_in"),
    SweepFieldSpec(("boundary_conditions",), "Ps_out", "Ps_out"),
    SweepFieldSpec(("droplet_injection",), "droplet_velocity_in", "droplet_velocity_in"),
    SweepFieldSpec(("droplet_injection",), "droplet_diameter_mean_in", "droplet_diameter_mean_in"),
    SweepFieldSpec(("droplet_injection",), "droplet_diameter_max_in", "droplet_diameter_max_in"),
    SweepFieldSpec(("models", "model_selection"), "critical_weber_number", "critical_weber_number"),
    SweepFieldSpec(("models", "model_selection"), "breakup_factor_mean", "breakup_factor_mean"),
    SweepFieldSpec(("models", "model_selection"), "breakup_factor_max", "breakup_factor_max"),
    SweepFieldSpec(("fluid",), "inlet_wetness", "inlet_wetness", optional=True),
)


def parse_numeric_token_list(raw_value: Any, *, optional: bool = False) -> list[float | None]:
    """Parse one numeric value or a delimiter-separated numeric token list.

    Accepted delimiters: comma, whitespace, semicolon, full-width comma, and
    Japanese comma.
    """
    if raw_value is None:
        return [None] if optional else []
    if isinstance(raw_value, (int, float)):
        return [float(raw_value)]
    if isinstance(raw_value, (list, tuple)):
        # Accept lists/tuples of numeric values (already saved cases)
        values: list[float] = []
        for elem in raw_value:
            if elem is None:
                if optional:
                    values.append(None)
                    continue
                raise ValueError(f"Field contains None but is not optional: {raw_value!r}")
            try:
                values.append(float(elem))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid numeric element {elem!r} in {raw_value!r}.") from exc
        return values

    text = str(raw_value).strip()
    if not text:
        return [None] if optional else []

    tokens = [token for token in _TOKEN_SPLIT_RE.split(text) if token]
    values: list[float] = []
    for token in tokens:
        try:
            values.append(float(token))
        except ValueError as exc:
            raise ValueError(f"Invalid numeric token {token!r} in {text!r}.") from exc
    return values


def _resolve_section(config: dict[str, Any], section_names: tuple[str, ...]) -> dict[str, Any] | None:
    for section_name in section_names:
        section = config.get(section_name)
        if isinstance(section, dict):
            return section
    return None


def _ensure_solver_compatible_config(raw_config: dict[str, Any]) -> dict[str, Any]:
    config = deepcopy(raw_config)
    if "model_selection" in config and "models" not in config:
        config["models"] = deepcopy(config["model_selection"])
    outputs = deepcopy(config.get("outputs", {}))
    outputs["write_csv"] = False
    outputs["write_json"] = False
    outputs["generate_plots"] = False
    if "output_directory" not in outputs and "output_dir" in outputs:
        outputs["output_directory"] = outputs["output_dir"]
    config["outputs"] = outputs
    return config


def _format_label_value(value: float | None) -> str:
    if value is None:
        return "None"
    return f"{float(value):.6g}"


def expand_multi_value_config(
    *,
    case_name: str,
    raw_config: dict[str, Any],
    max_run_count: int = MAX_SWEEP_RUNS,
) -> tuple[ExpandedRunConfig, ...]:
    """Expand a GUI-side config snapshot into immutable per-run configs."""
    base_config = _ensure_solver_compatible_config(raw_config)

    field_values: list[tuple[SweepFieldSpec, list[float | None]]] = []
    total_runs = 1
    for spec in SWEEP_FIELD_SPECS:
        section = _resolve_section(base_config, spec.section_names)
        raw_value = None if section is None else section.get(spec.field_name)
        values = parse_numeric_token_list(raw_value, optional=spec.optional)
        if not values:
            if spec.optional:
                values = [None]
            else:
                raise ValueError(f"Field {spec.field_name!r} requires at least one numeric value.")
        field_values.append((spec, values))
        total_runs *= len(values)

    if total_runs > max_run_count:
        raise ValueError(
            f"Expanded parameter sweep has {total_runs} runs, exceeding the limit of {max_run_count}."
        )

    expanded: list[ExpandedRunConfig] = []
    value_lists = [values for _, values in field_values]
    for run_index, combination in enumerate(product(*value_lists), start=1):
        run_config = deepcopy(base_config)
        label_parts: list[str] = []
        for (spec, values), value in zip(field_values, combination, strict=True):
            section = _resolve_section(run_config, spec.section_names)
            if section is None:
                section = {}
                run_config[spec.section_names[0]] = section
            if value is None and spec.optional:
                section.pop(spec.field_name, None)
            elif value is not None:
                section[spec.field_name] = float(value)
            if len(values) > 1:
                label_parts.append(f"{spec.label}={_format_label_value(value)}")

        run_label = " | ".join(label_parts) if label_parts else case_name
        expanded.append(
            ExpandedRunConfig(run_index=run_index, run_label=run_label, config=run_config)
        )

    return tuple(expanded)


def execute_expanded_runs(
    *,
    case_name: str,
    expanded_runs: Iterable[ExpandedRunConfig],
    runner: Callable[[str], SimulationRunResult],
) -> MultiRunSimulationResult:
    """Write temporary YAML snapshots and execute the runner once per run."""
    labeled_runs: list[LabeledSimulationRun] = []

    with TemporaryDirectory(prefix="supersonic_atomizer_gui_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        for expanded_run in expanded_runs:
            snapshot_path = temp_dir / f"{case_name}_run_{expanded_run.run_index:03d}.yaml"
            snapshot_path.write_text(
                yaml.safe_dump(expanded_run.config, sort_keys=False),
                encoding="utf-8",
            )
            run_result = runner(str(snapshot_path))
            if run_result.simulation_result is None or run_result.status not in {"completed", "output-failed"}:
                failure_message = run_result.failure_message or run_result.status
                raise RuntimeError(
                    f"Run '{expanded_run.run_label}' failed during solve execution: {failure_message}"
                )
            labeled_runs.append(
                LabeledSimulationRun(
                    run_index=expanded_run.run_index,
                    run_label=expanded_run.run_label,
                    run_result=run_result,
                )
            )

    return MultiRunSimulationResult(case_name=case_name, runs=tuple(labeled_runs))