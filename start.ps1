# SafeRoute AI - Single Startup Script for Windows PowerShell
# Starts both Django REST backend (port 8000) and React Vite frontend (port 5173)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  SafeRoute AI: Risk-Aware Routing via Causal Inference   " -ForegroundColor Green
Write-Host "  Micro Project 14 (Integrated CO1, CO2, CO3, CO4, CO5)   " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

# 1. Locate and Validate Python Interpreter
$PythonPath = "python"
if (Test-Path ".\.venv\Scripts\python.exe") {
    try {
        & ".\.venv\Scripts\python.exe" -c "import sys" 2>$null
        if ($LASTEXITCODE -eq 0) {
            $PythonPath = ".\.venv\Scripts\python.exe"
            Write-Host "[✓] Using validated virtual environment: $PythonPath" -ForegroundColor Cyan
        } else {
            Write-Host "[!] Existing .venv is invalid or was copied from another machine." -ForegroundColor Yellow
            Write-Host "[!] Delete .venv and run: python -m venv .venv && pip install -r requirements.txt" -ForegroundColor Yellow
            Write-Host "[!] Falling back to system python..." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[!] Virtual environment check failed. Falling back to system python..." -ForegroundColor Yellow
    }
} else {
    Write-Host "[✓] Using system python: $PythonPath" -ForegroundColor Cyan
}

# 2. Check if Django & core dependencies exist
try {
    & $PythonPath -c "import django" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Django is not installed in '$PythonPath'!" -ForegroundColor Red
        Write-Host "[!] Run: pip install -r requirements.txt" -ForegroundColor Yellow
        Write-Host "[!] See SETUP_INSTRUCTIONS.md for full step-by-step guidance." -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "[ERROR] Could not execute Python interpreter: $PythonPath" -ForegroundColor Red
    exit 1
}

# 3. Check Database / Migrations
Write-Host "[+] Running database migrations..." -ForegroundColor Yellow
& $PythonPath backend/manage.py migrate --noinput

# 4. Check Frontend dependencies
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "[+] Installing frontend dependencies (npm install)..." -ForegroundColor Yellow
    npm --prefix frontend install
}

# 5. Start Django Backend Server in background process
Write-Host "[+] Launching Django REST Backend on http://localhost:8000..." -ForegroundColor Cyan
$BackendJob = Start-Process -FilePath $PythonPath -ArgumentList "backend/manage.py runserver 0.0.0.0:8000" -PassThru

# 6. Start Vite Frontend Server
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
