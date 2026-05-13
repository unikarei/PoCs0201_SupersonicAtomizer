REM ------------------------------------------------------------------------------
REM Purpose:
REM   Start Docker Compose (dev mode, foreground) for SupersonicAtomizer.
REM   Builds and runs the stack, showing logs in the terminal.
REM ------------------------------------------------------------------------------
@echo off
setlocal enableextensions
set "RUN31_SCRIPT_VERSION=v0.0.1"

cd /d %~dp0

echo ========================================
echo   SupersonicAtomizer Docker Compose (Dev)
echo ========================================
echo Script version : %RUN31_SCRIPT_VERSION%
echo Project root   : %CD%
echo.

REM Start Docker Compose (foreground)
docker compose up --build

endlocal