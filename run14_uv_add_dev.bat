@echo off
setlocal enableextensions
set "RUN14_SCRIPT_VERSION=v0.0.2"

cd /d %~dp0

where uv >nul 2>nul
if errorlevel 1 (
    echo [Error] uv is not installed or not in PATH.
    exit /b 1
)

if "%~1"=="" (
    echo Usage: run14_uv_add_dev.bat ^<package^> [package2 ...]
    echo.
    echo Examples:
    echo   run14_uv_add_dev.bat ruff
    echo   run14_uv_add_dev.bat mypy ruff
    exit /b 1
)

echo ========================================
echo           uv add dev Script
echo ========================================
echo Script version : %RUN14_SCRIPT_VERSION%
echo Project root   : %CD%
echo.
echo Running: uv add --group dev %*
uv add --group dev %*
set "EXIT_CODE=%ERRORLEVEL%"
echo.
if "%EXIT_CODE%"=="0" (
    echo [OK] Dev dependency added successfully.
) else (
    echo [Error] uv add --group dev failed with exit code %EXIT_CODE%.
)
exit /b %EXIT_CODE%
