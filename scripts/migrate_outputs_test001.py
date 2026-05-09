"""Move existing outputs from outputs/TEST001/... to outputs/<project>/<case>/...

This script finds run directories under outputs/TEST001 and moves each
run directory to outputs/<project>/<case>/<run-id> preserving directory
structure expected by the application.

Run from the repository root:

    python scripts/migrate_outputs_test001.py

"""
from pathlib import Path
import shutil
import sys

ROOT = Path.cwd()
SRC_ROOT = ROOT / "outputs" / "TEST001"
DST_ROOT = ROOT / "outputs"

if not SRC_ROOT.exists():
    print(f"Source root {SRC_ROOT} does not exist. Nothing to do.")
    sys.exit(0)

moved = []
errors = []
for run_dir in SRC_ROOT.rglob("run-*"):
    if not run_dir.is_dir():
        continue
    # Expect path like outputs/TEST001/<project>/<case>/run-...
    try:
        rel = run_dir.relative_to(SRC_ROOT)
    except Exception as e:
        errors.append((run_dir, f"relative error: {e}"))
        continue
    parts = rel.parts
    if len(parts) < 3:
        # If run is directly under outputs/TEST001 or unexpected layout,
        # place it under outputs/UNCATEGORISED/<run_dir_name>
        dest_parent = DST_ROOT / "UNCATEGORISED"
    else:
        project = parts[0]
        case = parts[1]
        dest_parent = DST_ROOT / project / case
    dest_parent.mkdir(parents=True, exist_ok=True)
    dest = dest_parent / run_dir.name
    if dest.exists():
        errors.append((run_dir, f"destination already exists: {dest}"))
        continue
    try:
        shutil.move(str(run_dir), str(dest_parent))
        moved.append((str(run_dir), str(dest)))
    except Exception as e:
        errors.append((run_dir, str(e)))

print("Migration complete.")
print(f"Moved: {len(moved)} runs")
for s, d in moved:
    print(f"  {s} -> {d}")
if errors:
    print(f"Errors: {len(errors)}")
    for r, err in errors:
        print(f"  {r}: {err}")
else:
    print("No errors.")
