"""Small helper to move a legacy run directory into a Project/Case layout.

Usage:
    python scripts/migrate_run_to_case.py <run_dir> <project> <case>

This performs a safe move (rename) when possible; falls back to copy+remove.
"""
import shutil
import sys
from pathlib import Path


def main(argv):
    if len(argv) < 4:
        print("Usage: migrate_run_to_case.py <run_dir> <project> <case>")
        return 2
    run_dir = Path(argv[1])
    project = argv[2]
    case = argv[3]
    if not run_dir.is_dir():
        print(f"Run directory not found: {run_dir}")
        return 2
    dest = Path("outputs") / project / case / run_dir.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        run_dir.rename(dest)
        print(f"Moved {run_dir} -> {dest}")
    except Exception:
        print("Rename failed; attempting copy and remove...")
        shutil.copytree(run_dir, dest)
        shutil.rmtree(run_dir)
        print(f"Copied {run_dir} -> {dest} and removed source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
