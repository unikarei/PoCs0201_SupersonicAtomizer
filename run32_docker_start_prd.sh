#!/bin/bash
# ------------------------------------------------------------------------------
# Purpose:
#   Start Docker Compose (prod mode, detached) for SupersonicAtomizer.
#   Builds and runs the stack in the background.
# ------------------------------------------------------------------------------
set -eu
SCRIPT_VERSION="v0.0.1"

cd "$(dirname "$0")"

printf '========================================\n'
printf '  SupersonicAtomizer Docker Compose (Prod)\n'
printf '========================================\n'
printf 'Script version : %s\n' "$SCRIPT_VERSION"
printf 'Project root   : %s\n' "$PWD"
printf '\n'

docker compose up --build -d
