@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo   SEO Spy Agent - Automated Launcher
echo ========================================

:: 1. Backend Activation & Run
echo [1] Initializing Backend environment...
if not exist "venv_working" (
    echo [!] Virtual environment not found. Creating it...
    python -m venv venv_working
)

echo [2] Activating Virtual Environment...
set VENV_PYTHON=venv_working\Scripts\python.exe

echo [3] Starting all services...
%VENV_PYTHON% run_project.py %*

if %errorlevel% neq 0 (
    echo [!] Application exited with error code %errorlevel%
    pause
)
