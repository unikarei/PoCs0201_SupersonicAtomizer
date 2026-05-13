#!/usr/bin/env bash
# Launch the FastAPI-based Supersonic Atomizer GUI (P25-T06)
# Usage: bash run21_fastapi_gui.sh
#
# The server starts on http://127.0.0.1:8502 and (on macOS/Linux with
# xdg-open / open) attempts to open the default browser automatically.
# Press Ctrl+C to stop.

set -e

PORT=8502
echo "Starting FastAPI GUI on http://127.0.0.1:${PORT} ..."
echo "Press Ctrl+C to stop."
echo

# Open browser in background if possible
if command -v xdg-open &>/dev/null; then
  sleep 1 && xdg-open "http://127.0.0.1:${PORT}" &
elif command -v open &>/dev/null; then
  sleep 1 && open "http://127.0.0.1:${PORT}" &
fi

uv run uvicorn supersonic_atomizer.gui.fastapi_app:app \
  --host 127.0.0.1 --port "${PORT}" --reload
