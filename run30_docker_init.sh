#!/bin/bash
# ------------------------------------------------------------------------------
# Purpose:
#   Initialize Docker build environment for SupersonicAtomizer.
#   Checks for Dockerfile and compose.yml, shows status.
# ------------------------------------------------------------------------------
set -eu
SCRIPT_VERSION="v0.0.1"

cd "$(dirname "$0")"

printf '========================================\n'
printf '  SupersonicAtomizer Docker Init\n'
printf '========================================\n'
printf 'Script version : %s\n' "$SCRIPT_VERSION"
printf 'Project root   : %s\n' "$PWD"
printf '\n'

if [ ! -f Dockerfile ]; then
  echo "[INFO] Dockerfile not found. Please generate or copy it first."
  echo "        See docs/ for Dockerfile template."
  exit 1
fi
if [ ! -f compose.yml ]; then
  echo "[INFO] compose.yml not found. Please generate or copy it first."
  echo "        See docs/ for compose.yml template."
  exit 1
fi

echo "[OK] Dockerfile and compose.yml are present."
echo "Ready for docker compose build."
echo "Next: run31_docker_start_dev.sh or run32_docker_start_prd.sh"
