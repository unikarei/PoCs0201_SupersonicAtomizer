#!/usr/bin/env bash
set -euo pipefail
RUN14_SCRIPT_VERSION="v0.0.2"

if [ "$0" != "${BASH_SOURCE[0]}" ]; then
    printf 'Error: run14_uv_add_dev.sh must be executed directly, not sourced.\n' >&2
    return 1 2>/dev/null || exit 1
fi

cd "$(dirname "$0")" || exit 1

if ! command -v uv >/dev/null 2>&1; then
    echo "[Error] uv is not installed or not in PATH." >&2
    exit 1
fi

if [ $# -eq 0 ]; then
    echo "Usage: ./run14_uv_add_dev.sh <package> [package2 ...]"
    echo
    echo "Examples:"
    echo "  ./run14_uv_add_dev.sh ruff"
    echo "  ./run14_uv_add_dev.sh mypy ruff"
    exit 1
fi

cat <<EOF
========================================
          uv add dev Script
========================================
Script version : $RUN14_SCRIPT_VERSION
Project root   : $(pwd)

EOF

echo "Running: uv add --group dev $*"
uv add --group dev "$@"
echo
echo "[OK] Dev dependency added successfully."
