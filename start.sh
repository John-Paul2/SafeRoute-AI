#!/usr/bin/env bash
# SafeRoute AI - Single Start Script for Linux / macOS
set -e

echo "=========================================================="
echo "  SafeRoute AI: Single Start Script"
echo "  Micro Project 14 (Integrated CO1, CO2, CO3, CO4, CO5)"
echo "=========================================================="

PYTHON="python3"
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON=".venv/Scripts/python.exe"
fi

echo "[*] Using Python: $PYTHON"
$PYTHON backend/manage.py migrate --noinput

echo "[*] Starting Django REST Backend on http://localhost:8000..."
$PYTHON backend/manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!

trap "kill $BACKEND_PID 2>/dev/null || true; exit" SIGINT SIGTERM EXIT

echo "[*] Starting Vite Frontend on http://localhost:5173..."
npm --prefix frontend run dev
