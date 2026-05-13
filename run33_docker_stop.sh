#!/bin/bash
# ------------------------------------------------------------------------------
# Purpose:
#   Stop and remove all Docker Compose containers for SupersonicAtomizer.
# ------------------------------------------------------------------------------
set -eu
SCRIPT_VERSION="v0.0.1"

cd "$(dirname "$0")"

printf '========================================\n'
printf '  SupersonicAtomizer Docker Compose Stop\n'
printf '========================================\n'
printf 'Script version : %s\n' "$SCRIPT_VERSION"
printf 'Project root   : %s\n' "$PWD"
printf '\n'

docker compose down
