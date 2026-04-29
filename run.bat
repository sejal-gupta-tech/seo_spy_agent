@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo   SEO Spy Agent - Automated Launcher
echo ========================================

:: 1. Backend Activation & Run
:: We use run_project.py which handles setup, smoke checks, and starting uvicorn.
:: It will also start the frontend by default now.
echo [1] Initializing Backend environment...
if not exist "venv" (
    echo [!] Virtual environment not found. Creating it...
    python -m venv venv
)

echo [2] Activating Virtual Environment...
call venv\Scripts\activate

echo [3] Starting all services...
:: run_project.py will now start both backend and frontend.
:: We use 'python' here which refers to the venv python after activation.
python run_project.py %*

if %errorlevel% neq 0 (
    echo [!] Application exited with error code %errorlevel%
    pause
)
