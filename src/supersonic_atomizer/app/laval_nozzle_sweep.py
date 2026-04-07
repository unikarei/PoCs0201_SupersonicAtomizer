"""Application-level Laval-nozzle back-pressure sweep utility."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import math

import matplotlib

matplotlib.use("Agg")

from matplotlib import pyplot as plt

from supersonic_atomizer.config import (
    apply_config_defaults,
    load_raw_case_config,
    translate_case_config,
    validate_raw_config_schema,
    validate_semantic_config,
)
from supersonic_atomizer.domain import BoundaryConditionConfig, CaseConfig
from supersonic_atomizer.geometry import build_geometry_model
from supersonic_atomizer.solvers.gas import solve_quasi_1d_gas_flow
from supersonic_atomizer.solvers.gas.state_updates import (
    compute_area_mach_relation,
    compute_normal_shock_downstream_mach,
    compute_normal_shock_static_pressure_ratio,
    compute_post_shock_total_pressure,
    compute_static_pressure,
    solve_subsonic_mach_from_area_ratio,
    solve_supersonic_mach_from_area_ratio,
)
from supersonic_atomizer.thermo import select_thermo_provider


@dataclass(frozen=True, slots=True)
class LavalSweepCurve:
    """One back-pressure sweep curve for textbook Laval-nozzle regime comparison."""

    label: str
    back_pressure: float
    selected_branch: str
    x_values: tuple[float, ...]
    pressure_ratio_values: tuple[float, ...]
    shock_location_x: float | None = None


@dataclass(frozen=True, slots=True)
class LavalSweepResult:
    """Structured result for one Laval-nozzle back-pressure sweep."""

    case_path: str
    plot_path: str
    summary_path: str
    report_path: str
    curves: tuple[LavalSweepCurve, ...]
    validation_status: str
    validation_observations: tuple[str, ...]
    notes: tuple[str, ...]


def _curve_map(curves: tuple[LavalSweepCurve, ...]) -> dict[str, LavalSweepCurve]:
    return {curve.label: curve for curve in curves}


def _profiles_match(left: LavalSweepCurve, right: LavalSweepCurve, *, tolerance: float = 1.0e-10) -> bool:
    if left.x_values != right.x_values:
        return False
    return all(abs(a - b) <= tolerance for a, b in zip(left.pressure_ratio_values, right.pressure_ratio_values))


def _evaluate_pressure_ratio_validation(curves: tuple[LavalSweepCurve, ...]) -> tuple[str, tuple[str, ...]]:
    """Evaluate qualitative textbook agreement for the x vs p/p0 sweep family."""

    curve_map = _curve_map(curves)
    observations: list[str] = []
    failures: list[str] = []

    expected_branches = {
        "b": "subsonic_internal",
        "d": "exit_normal_shock",
        "g": "internal_normal_shock",
        "h": "internal_normal_shock",
        "j": "fully_supersonic_internal",
        "k": "fully_supersonic_internal",
    }
    for label, expected_branch in expected_branches.items():
        actual_branch = curve_map[label].selected_branch
        if actual_branch != expected_branch:
            failures.append(f"Curve {label} selected '{actual_branch}' instead of '{expected_branch}'.")
        else:
            observations.append(f"Curve {label} selected the expected branch '{expected_branch}'.")

    exit_ratios = {label: curve_map[label].pressure_ratio_values[-1] for label in expected_branches}
    if not (exit_ratios["b"] > exit_ratios["h"] > exit_ratios["g"] > exit_ratios["d"] > exit_ratios["j"]):
        failures.append("Exit pressure-ratio ordering does not follow b > h > g > d > j.")
    else:
        observations.append("Exit pressure ratios follow the expected ordering b > h > g > d > j.")

    if abs(exit_ratios["j"] - exit_ratios["k"]) > 1.0e-10:
        failures.append("Curves j and k do not share the same exit pressure ratio.")
    else:
        observations.append("Curves j and k share the same exit pressure ratio, consistent with the same internal branch.")

    if not _profiles_match(curve_map["j"], curve_map["k"]):
        failures.append("Curves j and k do not share the same internal pressure-ratio profile.")
    else:
        observations.append("Curves j and k share the same internal pressure-ratio profile.")

    shock_g = curve_map["g"].shock_location_x
    shock_h = curve_map["h"].shock_location_x
    shock_d = curve_map["d"].shock_location_x
    if shock_g is None or shock_h is None or shock_d is None:
        failures.append("One or more shock-bearing curves are missing a reported shock location.")
    else:
        if not (shock_h < shock_g < shock_d):
            failures.append("Shock locations do not move downstream in the expected order h < g < d.")
        else:
            observations.append("Shock locations move downstream in the expected order h < g < d.")

    for label, curve in curve_map.items():
        if not all(value > 0.0 and math.isfinite(value) for value in curve.pressure_ratio_values):
            failures.append(f"Curve {label} contains nonphysical pressure-ratio values.")

    status = "pass" if not failures else "warn"
    if failures:
        observations.extend(failures)
    return status, tuple(observations)


def _write_pressure_ratio_report(
    *,
    case_path: str,
    curves: tuple[LavalSweepCurve, ...],
    output_root: Path,
    plot_path: Path,
    summary_path: Path,
    notes: tuple[str, ...],
) -> tuple[str, str, tuple[str, ...]]:
    """Write a Markdown validation report for the Laval-nozzle x vs p/p0 sweep."""

    validation_status, validation_observations = _evaluate_pressure_ratio_validation(curves)
    report_path = output_root / "laval_nozzle_p_over_p0_report.md"
    lines = [
        "# Laval Nozzle $x$ vs $p/p_0$ Validation Report",
        "",
        f"- Case: {case_path}",
        f"- Plot: {plot_path}",
        f"- Summary JSON: {summary_path}",
        f"- Validation status: {validation_status}",
        "",
        "## Sweep Curves",
        "",
        "| Curve | Back pressure [Pa] | Branch | Shock location x [m] | Exit $p/p_0$ |",
        "|---|---:|---|---:|---:|",
    ]
    for curve in curves:
        shock_text = "-" if curve.shock_location_x is None else f"{curve.shock_location_x:.6f}"
        lines.append(
            f"| {curve.label} | {curve.back_pressure:.6f} | {curve.selected_branch} | {shock_text} | {curve.pressure_ratio_values[-1]:.6f} |"
        )

    lines.extend([
        "",
        "## Qualitative Assessment",
        "",
    ])
    for observation in validation_observations:
        lines.append(f"- {observation}")

    lines.extend([
        "",
        "## Notes",
        "",
    ])
    for note in notes:
        lines.append(f"- {note}")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(report_path), validation_status, validation_observations


def _load_case_config(case_path: str) -> CaseConfig:
    raw_config = load_raw_case_config(case_path)
    validated_schema = validate_raw_config_schema(raw_config)
    validated_semantics = validate_semantic_config(validated_schema)
    normalized = apply_config_defaults(validated_semantics)
    return translate_case_config(normalized)


@dataclass(frozen=True, slots=True)
class _LavalGeometryInfo:
    throat_x: float
    throat_area: float
    first_diverging_x: float


def _locate_laval_geometry(case_config: CaseConfig) -> tuple[object, _LavalGeometryInfo]:
    geometry_model = build_geometry_model(case_config.geometry)
    source_points = list(geometry_model.area_profile_data)
    area_values = [point[1] for point in source_points]
    throat_area = min(area_values)
    throat_index = area_values.index(throat_area)
    if throat_index == 0 or throat_index == len(source_points) - 1:
        raise ValueError("The supplied case is not a supported converging-diverging Laval-nozzle geometry.")
    return geometry_model, _LavalGeometryInfo(
        throat_x=source_points[throat_index][0],
        throat_area=throat_area,
        first_diverging_x=source_points[throat_index + 1][0],
    )


def _branch_from_diagnostics(messages: tuple[str, ...]) -> str:
    for message in messages:
        if message.startswith("selected_branch="):
            return message.split("=", 1)[1]
    return "unknown"


def _shock_location_from_diagnostics(messages: tuple[str, ...]) -> float | None:
    for message in messages:
        if message.startswith("shock_location_x="):
            return float(message.split("=", 1)[1])
    return None


def _compute_internal_shock_exit_pressure(
    *,
    geometry_model,
    laval_geometry: _LavalGeometryInfo,
    shock_x: float,
    total_pressure: float,
    total_temperature: float,
    heat_capacity_ratio: float,
) -> float:
    del total_temperature
    shock_area = geometry_model.area_at(shock_x)
    upstream_mach_number = solve_supersonic_mach_from_area_ratio(
        shock_area / laval_geometry.throat_area,
        heat_capacity_ratio,
    )
    downstream_mach_number = compute_normal_shock_downstream_mach(
        upstream_mach_number,
        heat_capacity_ratio,
    )
    downstream_total_pressure = compute_post_shock_total_pressure(
        total_pressure,
        upstream_mach_number,
        heat_capacity_ratio,
    )
    effective_throat_area = shock_area / compute_area_mach_relation(
        downstream_mach_number,
        heat_capacity_ratio,
    )
    exit_area = geometry_model.area_at(geometry_model.x_end)
    exit_area_ratio = exit_area / effective_throat_area
    exit_mach_number = solve_subsonic_mach_from_area_ratio(exit_area_ratio, heat_capacity_ratio)
    return compute_static_pressure(downstream_total_pressure, exit_mach_number, heat_capacity_ratio)


def _derive_back_pressures(case_config: CaseConfig) -> dict[str, float]:
    geometry_model, laval_geometry = _locate_laval_geometry(case_config)
    thermo_provider = select_thermo_provider(case_config)
    gamma = getattr(thermo_provider, "heat_capacity_ratio")
    total_pressure = case_config.boundary_conditions.Pt_in
    total_temperature = case_config.boundary_conditions.Tt_in
    exit_area = geometry_model.area_at(geometry_model.x_end)
    exit_supersonic_mach = solve_supersonic_mach_from_area_ratio(exit_area / laval_geometry.throat_area, gamma)
    exit_supersonic_pressure = compute_static_pressure(total_pressure, exit_supersonic_mach, gamma)
    exit_shock_pressure = exit_supersonic_pressure * compute_normal_shock_static_pressure_ratio(
        exit_supersonic_mach,
        gamma,
    )
    near_throat_x = 0.5 * (laval_geometry.throat_x + laval_geometry.first_diverging_x)
    near_throat_exit_pressure = _compute_internal_shock_exit_pressure(
        geometry_model=geometry_model,
        laval_geometry=laval_geometry,
        shock_x=near_throat_x,
        total_pressure=total_pressure,
        total_temperature=total_temperature,
        heat_capacity_ratio=gamma,
    )
    shock_band = near_throat_exit_pressure - exit_shock_pressure
    if shock_band <= 0.0:
        raise ValueError("Could not derive a valid internal-normal-shock pressure envelope.")

    back_pressures = {
        "b": min(total_pressure * 0.90, near_throat_exit_pressure * 1.08),
        "d": exit_shock_pressure,
        "g": exit_shock_pressure + 0.30 * shock_band,
        "h": exit_shock_pressure + 0.65 * shock_band,
        "j": max(exit_supersonic_pressure * 0.90, total_pressure * 0.10),
        "k": max(exit_supersonic_pressure * 0.60, total_pressure * 0.05),
    }
    return back_pressures


def run_laval_nozzle_back_pressure_sweep(
    *,
    case_path: str,
    output_directory: str | None = None,
) -> LavalSweepResult:
    """Run a textbook-style Laval-nozzle internal sweep and write x vs p/p0 artifacts."""

    case_config = _load_case_config(case_path)
    thermo_provider = select_thermo_provider(case_config)
    back_pressures = _derive_back_pressures(case_config)
    output_root = Path(output_directory or "outputs/laval_nozzle_sweep")
    output_root.mkdir(parents=True, exist_ok=True)

    curves: list[LavalSweepCurve] = []
    for label in ("b", "d", "g", "h", "j", "k"):
        run_case = replace(
            case_config,
            boundary_conditions=BoundaryConditionConfig(
                Pt_in=case_config.boundary_conditions.Pt_in,
                Tt_in=case_config.boundary_conditions.Tt_in,
                Ps_out=back_pressures[label],
            ),
        )
        geometry_model = build_geometry_model(run_case.geometry)
        gas_solution = solve_quasi_1d_gas_flow(
            geometry_model=geometry_model,
            boundary_conditions=run_case.boundary_conditions,
            thermo_provider=thermo_provider,
        )
        curves.append(
            LavalSweepCurve(
                label=label,
                back_pressure=back_pressures[label],
                selected_branch=_branch_from_diagnostics(gas_solution.diagnostics.messages),
                shock_location_x=_shock_location_from_diagnostics(gas_solution.diagnostics.messages),
                x_values=gas_solution.x_values,
                pressure_ratio_values=tuple(
                    pressure / run_case.boundary_conditions.Pt_in
                    for pressure in gas_solution.pressure_values
                ),
            )
        )

    plot_path = output_root / "laval_nozzle_x_vs_p_over_p0.png"
    figure, axis = plt.subplots(figsize=(8.0, 5.0))
    for curve in curves:
        axis.plot(curve.x_values, curve.pressure_ratio_values, linewidth=2.0, label=curve.label)
    axis.set_xlabel("x [m]")
    axis.set_ylabel("p/p0 [-]")
    axis.set_title("Laval nozzle internal pressure distributions")
    axis.grid(True)
    axis.legend(title="regime")
    figure.tight_layout()
    figure.savefig(plot_path)
    plt.close(figure)

    summary_path = output_root / "laval_nozzle_sweep_summary.json"
    summary_payload = {
        "case_path": case_path,
        "validation": {},
        "curves": [
            {
                "label": curve.label,
                "back_pressure": curve.back_pressure,
                "selected_branch": curve.selected_branch,
                "shock_location_x": curve.shock_location_x,
            }
            for curve in curves
        ],
    }

    notes = (
        "b: fully subsonic internal solution",
        "d: exit normal shock limit",
        "g/h: internal normal shock inside the diverging section",
        "j/k: fully supersonic internal solution family (same internal profile)",
    )
    report_path, validation_status, validation_observations = _write_pressure_ratio_report(
        case_path=case_path,
        curves=tuple(curves),
        output_root=output_root,
        plot_path=plot_path,
        summary_path=summary_path,
        notes=notes,
    )
    summary_payload["validation"] = {
        "status": validation_status,
        "observations": list(validation_observations),
        "report_path": report_path,
    }
    summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    return LavalSweepResult(
        case_path=case_path,
        plot_path=str(plot_path),
        summary_path=str(summary_path),
        report_path=report_path,
        curves=tuple(curves),
        validation_status=validation_status,
        validation_observations=validation_observations,
        notes=notes,
    )
