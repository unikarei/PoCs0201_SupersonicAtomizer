"""Simple case/geometry diagnostic helper.

Usage: python -m scripts.diagnose_case path/to/case.yaml
"""
from __future__ import annotations

import sys
import yaml

from supersonic_atomizer.config.schema import validate_raw_config_schema
from supersonic_atomizer.config.semantics import validate_semantic_config
from supersonic_atomizer.config.translator import translate_case_config
from supersonic_atomizer.geometry.geometry_model import build_geometry_model
from supersonic_atomizer.solvers.gas.quasi_1d_solver import _locate_supported_laval_geometry


def diagnose(case_path: str) -> int:
    with open(case_path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    print(f"Loaded: {case_path}")

    # Normalize: remove explicit nulls to emulate GUI/backend normalization
    def _strip_none(obj):
        if isinstance(obj, dict):
            return {k: _strip_none(v) for k, v in obj.items() if v is not None}
        if isinstance(obj, list):
            return [_strip_none(v) for v in obj if v is not None]
        return obj

    raw = _strip_none(raw)

    # Normalize multi-run Ps_out lists by selecting the first entry for diagnostic purposes
    if "boundary_conditions" in raw:
        bc = raw["boundary_conditions"]
        if "Ps_out" in bc and isinstance(bc["Ps_out"], list) and bc["Ps_out"]:
            bc["Ps_out"] = bc["Ps_out"][0]

    try:
        validate_raw_config_schema(raw)
        print("Raw schema: OK")
    except Exception as exc:
        print("Raw schema: FAILED ->", exc)
        return 2

    try:
        validate_semantic_config(raw)
        print("Semantic checks: OK")
    except Exception as exc:
        print("Semantic checks: FAILED ->", exc)
        return 3

    case = translate_case_config(raw)
    geom_cfg = case.geometry
    print(f"Geometry domain: x_start={geom_cfg.x_start}, x_end={geom_cfg.x_end}, n_cells={geom_cfg.n_cells}")
    print("Area definition type:", geom_cfg.area_definition.get("type"))
    points = list(zip(geom_cfg.area_definition.get("x", []), geom_cfg.area_definition.get("A", [])))
    print("Area table points:")
    for x, A in points:
        print(f"  x={x}, A={A}")

    try:
        geom_model = build_geometry_model(geom_cfg)
    except Exception as exc:
        print("Geometry build: FAILED ->", exc)
        return 4

    print("Geometry model built successfully.")

    laval = _locate_supported_laval_geometry(geom_model)
    if laval is None:
        print("Laval detection: NO — geometry is not a supported single-throat converging-diverging Laval nozzle.")
        return 5

    print("Laval detection: YES")
    print(f"  throat_x={laval.throat_x}, throat_area={laval.throat_area}, first_diverging_x={laval.first_diverging_x}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.diagnose_case path/to/case.yaml")
        raise SystemExit(2)
    raise SystemExit(diagnose(sys.argv[1]))
