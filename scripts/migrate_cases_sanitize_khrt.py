"""Migration: sanitize models.khrt_* fields in YAML case files.

Scans the `cases/` directory for YAML files and ensures that
`models.khrt_B0`, `models.khrt_B1`, and `models.khrt_Crt` are numeric
values (float) or arrays of floats rather than strings. Creates a
`.bak` backup for each modified file.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
import yaml

CASES_DIR = Path(__file__).resolve().parents[1] / "cases"
FIELDS = ("khrt_B0", "khrt_B1", "khrt_Crt")


def parse_numeric_or_list(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, list):
        out = []
        for v in value:
            try:
                out.append(float(v))
            except Exception:
                return value
        return out if len(out) != 1 else out[0]
    if isinstance(value, str):
        toks = [t for t in value.replace("，", ",").replace("、", ",").split(",") if t.strip()]
        if not toks:
            return None
        try:
            nums = [float(t) for t in (" ".join(toks)).split()]
        except Exception:
            return value
        return nums[0] if len(nums) == 1 else nums
    return value


def migrate_file(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf8")
        data = yaml.safe_load(text) or {}
    except Exception as e:
        print(f"Skipping {path}: failed to read/parse YAML: {e}")
        return False

    modified = False
    models = data.get("models")
    if not isinstance(models, dict):
        return False

    for fld in FIELDS:
        if fld in models:
            newv = parse_numeric_or_list(models[fld])
            if newv != models[fld]:
                print(f"Updating {path.name}: models.{fld} {models[fld]!r} -> {newv!r}")
                models[fld] = newv
                modified = True

    if modified:
        bak = path.with_suffix(path.suffix + ".bak")
        bak.write_text(text, encoding="utf8")
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf8")
    return modified


def main():
    if not CASES_DIR.exists():
        print(f"Cases directory not found: {CASES_DIR}")
        return 1
    changed = 0
    for p in sorted(CASES_DIR.glob("**/*.yaml")):
        if migrate_file(p):
            changed += 1
    print(f"Migration complete. Files modified: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
