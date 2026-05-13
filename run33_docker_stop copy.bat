REM ------------------------------------------------------------------------------
REM Purpose:
REM   Stop and remove all Docker Compose containers for SupersonicAtomizer.
REM ------------------------------------------------------------------------------
@echo off
setlocal enableextensions
set "RUN33_SCRIPT_VERSION=v0.0.1"

cd /d %~dp0

echo ========================================
echo   SupersonicAtomizer Docker Compose Stop
echo ========================================
echo Script version : %RUN33_SCRIPT_VERSION%
echo Project root   : %CD%
echo.

REM Stop and remove containers
docker compose down

endlocal