#!/bin/bash
# ------------------------------------------------------------------------------
# Purpose:
#   Start Docker Compose (dev mode, foreground) for SupersonicAtomizer.
#   Builds and runs the stack, showing logs in the terminal.
# ------------------------------------------------------------------------------
set -eu
SCRIPT_VERSION="v0.0.1"

cd "$(dirname "$0")"

printf '========================================\n'
printf '  SupersonicAtomizer Docker Compose (Dev)\n'
printf '========================================\n'
printf 'Script version : %s\n' "$SCRIPT_VERSION"
printf 'Project root   : %s\n' "$PWD"
printf '\n'

docker compose up --build
