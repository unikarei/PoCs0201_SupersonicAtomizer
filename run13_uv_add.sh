#!/usr/bin/env bash
set -euo pipefail
RUN13_SCRIPT_VERSION="v0.0.2"

if [ "$0" != "${BASH_SOURCE[0]}" ]; then
    printf 'Error: run13_uv_add.sh must be executed directly, not sourced.\n' >&2
    return 1 2>/dev/null || exit 1
fi

cd "$(dirname "$0")" || exit 1

if ! command -v uv >/dev/null 2>&1; then
    echo "[Error] uv is not installed or not in PATH." >&2
    exit 1
fi

if [ $# -eq 0 ]; then
    echo "Usage: ./run13_uv_add.sh <package> [package2 ...]"
    echo
    echo "Examples:"
    echo "  ./run13_uv_add.sh numpy"
    echo "  ./run13_uv_add.sh numpy scipy"
    exit 1
fi

cat <<EOF
========================================
             uv add Script
========================================
Script version : $RUN13_SCRIPT_VERSION
Project root   : $(pwd)

EOF

echo "Running: uv add $*"
uv add "$@"
echo
echo "[OK] Runtime dependency added successfully."
