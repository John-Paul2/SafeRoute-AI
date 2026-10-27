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
fi

echo "[*] Using Python: $PYTHON"

# Check if Django is installed
if ! $PYTHON -c "import django" &>/dev/null; then
    echo "[ERROR] Django is not installed in '$PYTHON'!"
    echo "[!] Run: pip install -r requirements.txt"
    echo "[!] See SETUP_INSTRUCTIONS.md for full guidance."
    exit 1
fi

# Check frontend node_modules
if [ ! -d "frontend/node_modules" ]; then
    echo "[+] Installing frontend dependencies (npm install)..."
    npm --prefix frontend install
fi

echo "[*] Applying migrations..."
$PYTHON backend/manage.py migrate --noinput

echo "[*] Starting Django REST Backend on http://localhost:8000..."
$PYTHON backend/manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!

trap "kill $BACKEND_PID 2>/dev/null || true; exit" SIGINT SIGTERM EXIT

echo "[*] Starting Vite Frontend on http://localhost:5173..."
npm --prefix frontend run dev
