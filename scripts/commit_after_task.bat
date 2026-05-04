@echo off
rem Commit all current changes with a message (used after completing a task)
setlocal enabledelayedexpansion

if not defined GIT_COMMIT_MSG (
  if "%~1"=="" (
    set "GIT_COMMIT_MSG=Automated commit after task completion"
  ) else (
    set "GIT_COMMIT_MSG=%~1"
  )
)

where git >nul 2>&1
if errorlevel 1 (
  echo git not found in PATH
  exit /b 2
)

echo Staging all changes...
git add -A

echo Committing with message: %GIT_COMMIT_MSG%
git commit -m "%GIT_COMMIT_MSG%"

echo Commit complete.
endlocal
