# SafeRoute AI - Single Startup Script for Windows PowerShell
# Starts both Django REST backend (port 8000) and React Vite frontend (port 5173)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  SafeRoute AI: Risk-Aware Routing via Causal Inference   " -ForegroundColor Green
Write-Host "  Micro Project 14 (Integrated CO1, CO2, CO3, CO4, CO5)   " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

# 1. Locate Python Interpreter
$PythonPath = "python"
if (Test-Path ".\.venv\Scripts\python.exe") {
    $PythonPath = ".\.venv\Scripts\python.exe"
    Write-Host "[✓] Using virtual environment: $PythonPath" -ForegroundColor Cyan
} else {
    Write-Host "[✓] Using system python: $PythonPath" -ForegroundColor Cyan
}

# 2. Check Database / Migrations
Write-Host "[+] Running database migrations..." -ForegroundColor Yellow
& $PythonPath backend/manage.py migrate --noinput

# 3. Pre-warm models check
Write-Host "[+] Verifying cached AI models (XGBoost, Bayesian Net, OSM Graph)..." -ForegroundColor Yellow
& $PythonPath backend/manage.py test api

# 4. Start Django Backend Server in background process
Write-Host "[+] Launching Django REST Backend on http://localhost:8000..." -ForegroundColor Cyan
$BackendJob = Start-Process -FilePath $PythonPath -ArgumentList "backend/manage.py runserver 0.0.0.0:8000" -PassThru

# 5. Start Vite Frontend Server
Write-Host "[+] Launching Vite Frontend on http://localhost:5173..." -ForegroundColor Cyan
Write-Host "[*] Press Ctrl+C in this terminal to terminate both processes." -ForegroundColor White

try {
    # Open browser after brief delay
    Start-Job -ScriptBlock {
        Start-Sleep -Seconds 3
        Start-Process "http://localhost:5173"
    } | Out-Null

    # Run frontend in current console
    npm --prefix frontend run dev
} finally {
    Write-Host "`n[!] Shutting down backend server..." -ForegroundColor Yellow
    if ($BackendJob -and -not $BackendJob.HasExited) {
        Stop-Process -Id $BackendJob.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[✓] All servers stopped cleanly." -ForegroundColor Green
}
