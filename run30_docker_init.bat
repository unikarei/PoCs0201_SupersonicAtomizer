REM ------------------------------------------------------------------------------
REM Purpose:
REM   Initialize Docker build environment for SupersonicAtomizer.
REM   Generates Dockerfile and compose.yml if missing, and shows status.
REM ------------------------------------------------------------------------------
@echo off
setlocal enableextensions
set "RUN30_SCRIPT_VERSION=v0.0.1"

cd /d %~dp0

echo ========================================
echo   SupersonicAtomizer Docker Init
echo ========================================
echo Script version : %RUN30_SCRIPT_VERSION%
echo Project root   : %CD%
echo.

REM Check for Dockerfile
if not exist Dockerfile (
	echo [INFO] Dockerfile not found. Please generate or copy it first.
	echo         See docs/ for Dockerfile template.
	exit /b 1
)

REM Check for compose.yml
if not exist compose.yml (
	echo [INFO] compose.yml not found. Please generate or copy it first.
	echo         See docs/ for compose.yml template.
	exit /b 1
)

echo [OK] Dockerfile and compose.yml are present.
echo Ready for docker compose build.
echo Next: run31_docker_start_dev.bat or run32_docker_start_prd.bat
echo.
endlocal
