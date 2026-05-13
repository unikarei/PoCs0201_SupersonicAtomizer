REM ------------------------------------------------------------------------------
REM Purpose:
REM   Show logs for all Docker Compose containers for SupersonicAtomizer.
REM ------------------------------------------------------------------------------
@echo off
setlocal enableextensions
set "RUN34_SCRIPT_VERSION=v0.0.1"

cd /d %~dp0

echo ========================================
echo   SupersonicAtomizer Docker Compose Logs
echo ========================================
echo Script version : %RUN34_SCRIPT_VERSION%
echo Project root   : %CD%
echo.

REM Show logs
docker compose logs -f

endlocal