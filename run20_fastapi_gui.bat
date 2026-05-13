@echo off
REM Launch the FastAPI-based Supersonic Atomizer GUI (P25-T06)
REM Usage: run21_fastapi_gui.bat
REM
REM The server starts on http://127.0.0.1:8502 and opens automatically
REM in the default browser.  Press Ctrl+C to stop.

set PORT=8502
echo Starting FastAPI GUI on http://127.0.0.1:%PORT% ...
echo Press Ctrl+C to stop.
echo.
rem Warn if OPENAI_API_KEY is not set in this environment. Do NOT embed secrets in this file.
if "%OPENAI_API_KEY%"=="" (
	echo WARNING: OPENAI_API_KEY is not set in this shell environment.
	echo To persist the key for future sessions, run:
	echo    setx OPENAI_API_KEY "sk-...your-key..."
	echo Or create a project .env file from .env.example and add your key there.
	echo The app will still start but chat features requiring LLM will be disabled.
)

start "FastAPI GUI Browser Waiter" cmd /c "powershell -NoProfile -ExecutionPolicy Bypass -Command ^& {$url='http://127.0.0.1:%PORT%'; for($i=0; $i -lt 50; $i++){ try { Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 1 ^| Out-Null; Start-Process $url; break } catch { Start-Sleep -Milliseconds 300 } }}"
uv run uvicorn supersonic_atomizer.gui.fastapi_app:app --host 127.0.0.1 --port %PORT% --reload
