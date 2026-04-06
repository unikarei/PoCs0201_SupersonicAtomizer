@echo off
setlocal enableextensions
set "RUN13_SCRIPT_VERSION=v0.0.2"

cd /d %~dp0

where uv >nul 2>nul
if errorlevel 1 (
    echo [Error] uv is not installed or not in PATH.
    exit /b 1
)

if "%~1"=="" (
    echo Usage: run13_uv_add.bat ^<package^> [package2 ...]
    echo.
    echo Examples:
    echo   run13_uv_add.bat numpy
    echo   run13_uv_add.bat numpy scipy
    exit /b 1
)

echo ========================================
echo              uv add Script
echo ========================================
echo Script version : %RUN13_SCRIPT_VERSION%
echo Project root   : %CD%
echo.
echo Running: uv add %*
uv add %*
set "EXIT_CODE=%ERRORLEVEL%"
echo.
if "%EXIT_CODE%"=="0" (
    echo [OK] Runtime dependency added successfully.
) else (
    echo [Error] uv add failed with exit code %EXIT_CODE%.
)
exit /b %EXIT_CODE%
