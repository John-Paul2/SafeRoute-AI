@echo off
echo ==========================================================
echo   SafeRoute AI: Single Start Script
echo   Micro Project 14 (Integrated CO1, CO2, CO3, CO4, CO5)
echo ==========================================================

set PYTHON=python
if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
)

echo [*] Using Python: %PYTHON%
echo [*] Applying migrations...
%PYTHON% backend\manage.py migrate --noinput

echo [*] Starting Django REST Backend on http://localhost:8000...
start "SafeRoute AI - Backend (port 8000)" %PYTHON% backend\manage.py runserver 0.0.0.0:8000

echo [*] Starting Vite Frontend on http://localhost:5173...
start http://localhost:5173
npm --prefix frontend run dev
