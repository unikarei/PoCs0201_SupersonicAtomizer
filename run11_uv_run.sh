#!/usr/bin/env bash
set -euo pipefail
RUN11_SCRIPT_VERSION="v0.0.2"

if [ "$0" != "${BASH_SOURCE[0]}" ]; then
    printf 'Error: run11_uv_run.sh must be executed directly, not sourced.\n' >&2
    return 1 2>/dev/null || exit 1
fi

cd "$(dirname "$0")" || exit 1

if ! command -v uv >/dev/null 2>&1; then
    echo "[Error] uv is not installed or not in PATH." >&2
    exit 1
fi

if [ $# -eq 0 ]; then
    echo "Usage: ./run11_uv_run.sh <yaml-case-file> [additional-args]"
    echo
    echo "Examples:"
    echo "  ./run11_uv_run.sh examples/air_nozzle.yaml"
    echo "  ./run11_uv_run.sh examples/steam_nozzle.yaml"
    echo "  ./run11_uv_run.sh examples/air_nozzle.yaml --startup-only"
    exit 1
fi

cat <<EOF
========================================
             uv run Script
========================================
Script version : $RUN11_SCRIPT_VERSION
Project root   : $(pwd)

EOF

echo "Running: uv run supersonic-atomizer $*"
uv run supersonic-atomizer "$@"
echo
echo "[OK] Simulation command completed successfully."
