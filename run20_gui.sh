#!/usr/bin/env bash
set -euo pipefail
RUN20_SCRIPT_VERSION="v0.0.1"

if [ "$0" != "${BASH_SOURCE[0]}" ]; then
    printf 'Error: run20_gui.sh must be executed directly, not sourced.\n' >&2
    return 1 2>/dev/null || exit 1
fi

cd "$(dirname "$0")" || exit 1

if ! command -v uv >/dev/null 2>&1; then
    echo "[Error] uv is not installed or not in PATH." >&2
    exit 1
fi

cat <<EOF
========================================
         GUI Launcher Script
========================================
Script version : $RUN20_SCRIPT_VERSION
Project root   : $(pwd)

EOF

echo "Running: uv run streamlit run src/supersonic_atomizer/gui/streamlit_app.py"
uv run streamlit run src/supersonic_atomizer/gui/streamlit_app.py
echo
echo "[OK] GUI exited successfully."
