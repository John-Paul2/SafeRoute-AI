@echo off
setlocal enabledelayedexpansion
echo ==========================================================
echo   SafeRoute AI: Single Start Script
echo   Micro Project 14 (Integrated CO1, CO2, CO3, CO4, CO5)
echo ==========================================================

set PYTHON=python

REM 1. Check if .venv exists and is valid
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -c "import sys" >nul 2>&1
    if errorlevel 1 (
        echo [!] WARNING: Existing .venv is invalid or was copied from another PC.
        echo [!] Virtual environments cannot be copied across machines.
        echo [!] Please delete .venv and create a fresh one:
        echo        rmdir /s /q .venv
        echo        python -m venv .venv
        echo        .venv\Scripts\pip install -r requirements.txt
        echo [!] See SETUP_INSTRUCTIONS.md for full guidance.
        pause
        exit /b 1
    ) else (
        set PYTHON=.venv\Scripts\python.exe
    )
)

echo [*] Using Python: %PYTHON%

REM 2. Verify dependencies (Django)
%PYTHON% -c "import django" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Dependencies not found in %PYTHON%!
    echo Please install dependencies first:
    echo    pip install -r requirements.txt
    echo See SETUP_INSTRUCTIONS.md for details.
    pause
    exit /b 1
)

REM 3. Verify node_modules in frontend
if not exist "frontend\node_modules\" (
    echo [*] Installing frontend dependencies (npm install)...
    call npm --prefix frontend install
)

echo [*] Applying migrations...
%PYTHON% backend\manage.py migrate --noinput
if errorlevel 1 (
    echo [ERROR] Database migration failed.
    pause
    exit /b 1
)

echo [*] Starting Django REST Backend on http://localhost:8000...
start "SafeRoute AI - Backend (port 8000)" cmd /k "%PYTHON% backend\manage.py runserver 0.0.0.0:8000"

echo [*] Starting Vite Frontend on http://localhost:5173...
start http://localhost:5173
call npm --prefix frontend run dev
