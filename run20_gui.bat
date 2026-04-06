@echo off
setlocal enableextensions
set "RUN20_SCRIPT_VERSION=v0.0.1"

cd /d %~dp0

where uv >nul 2>nul
if errorlevel 1 (
    echo [Error] uv is not installed or not in PATH.
    exit /b 1
)

echo ========================================
echo          GUI Launcher Script
echo ========================================
echo Script version : %RUN20_SCRIPT_VERSION%
echo Project root   : %CD%
echo.
echo Running: uv run streamlit run src/supersonic_atomizer/gui/streamlit_app.py
uv run streamlit run src/supersonic_atomizer/gui/streamlit_app.py
set "EXIT_CODE=%ERRORLEVEL%"
echo.
if "%EXIT_CODE%"=="0" (
    echo [OK] GUI exited successfully.
) else (
    echo [Error] GUI exited with code %EXIT_CODE%.
)
exit /b %EXIT_CODE%
