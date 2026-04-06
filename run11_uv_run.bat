@echo off
setlocal enableextensions
set "RUN11_SCRIPT_VERSION=v0.0.2"

cd /d %~dp0

where uv >nul 2>nul
if errorlevel 1 (
    echo [Error] uv is not installed or not in PATH.
    exit /b 1
)

if "%~1"=="" (
    echo Usage: run11_uv_run.bat ^<yaml-case-file^> [additional-args]
    echo.
    echo Examples:
    echo   run11_uv_run.bat examples\air_nozzle.yaml
    echo   run11_uv_run.bat examples\steam_nozzle.yaml
    echo   run11_uv_run.bat examples\air_nozzle.yaml --startup-only
    exit /b 1
)

echo ========================================
echo              uv run Script
echo ========================================
echo Script version : %RUN11_SCRIPT_VERSION%
echo Project root   : %CD%
echo.
echo Running: uv run supersonic-atomizer %*
uv run supersonic-atomizer %*
set "EXIT_CODE=%ERRORLEVEL%"
echo.
if "%EXIT_CODE%"=="0" (
    echo [OK] Simulation command completed successfully.
) else (
    echo [Error] Simulation command failed with exit code %EXIT_CODE%.
)
exit /b %EXIT_CODE%
