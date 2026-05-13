REM ------------------------------------------------------------------------------
REM Purpose:
REM   Start Docker Compose (prod mode, detached) for SupersonicAtomizer.
REM   Builds and runs the stack in the background.
REM ------------------------------------------------------------------------------
@echo off
setlocal enableextensions
set "RUN32_SCRIPT_VERSION=v0.0.1"

cd /d %~dp0

echo ========================================
echo   SupersonicAtomizer Docker Compose (Prod)
echo ========================================
echo Script version : %RUN32_SCRIPT_VERSION%
echo Project root   : %CD%
echo.

REM Start Docker Compose (detached)
docker compose up --build -d

endlocal