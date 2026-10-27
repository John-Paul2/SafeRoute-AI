# SafeRoute AI — Cross-Device Setup & Troubleshooting Guide

> **Micro Project 14**: AI-Based Road Accident Prediction (Traffic Management & Insurance Underwriting)  
> **Target OS**: Windows 10/11, macOS, Linux  
> **Python Compatibility**: Python 3.10.x or 3.11.x (64-bit)  
> **Node.js Compatibility**: Node.js v18.x or v20.x LTS

---

## 1. Why Did the Backend Fail on Your Friend's Laptop?

If the backend failed when transferred to another laptop, it is almost certainly due to one of these **3 common issues**:

### Issue 1: The Copied `.venv` Trap (Most Common — 95% of cases)
* **What happened**: The project was copied via a ZIP file, USB flash drive, or cloud drive with the `.venv` folder included.
* **Why it fails**: Python virtual environments are **machine-specific and non-portable**. Every executable and script in `.venv` contains hardcoded absolute paths pointing to the original computer (e.g., `C:\Users\LENOVO\...`).
* **The Error**: When your friend runs `python` or `start.bat`, Windows throws:
  ```text
  Fatal error in launcher: Unable to create process using '"C:\Users\LENOVO\AppData\..."'
  ```
* **The Fix**: **Never copy `.venv`!** Delete the `.venv` folder on your friend's laptop and create a fresh one (see Step 2 below).

---

### Issue 2: Incompatible Python Version (Python 3.12 or 3.13)
* **What happened**: Your friend installed the newest Python release (Python 3.12 or 3.13) from python.org or the Microsoft Store.
* **Why it fails**: Heavy geospatial, ML, and Bayesian libraries (`osmnx`, `geopandas`, `shapely`, `pyarrow`, `pgmpy`) rely on pre-compiled C-extensions. As of now, these packages require **Python 3.10 or 3.11**. On Python 3.12+, `pip install` fails with `Microsoft Visual C++ 14.0 or greater is required`.
* **The Fix**: Install **Python 3.11** (64-bit) from [python.org](https://www.python.org/downloads/release/python-3119/) and ensure **"Add python.exe to PATH"** is checked.

---

### Issue 3: PowerShell Script Execution Policy Blocked
* **What happened**: Your friend double-clicked or ran `.\start.ps1`.
* **Why it fails**: Windows blocks unsigned PowerShell scripts by default for security.
* **The Error**:
  ```text
  File ...\start.ps1 cannot be loaded because running scripts is disabled on this system.
  ```
* **The Fix**: Use `start.bat` instead, or run:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\start.ps1
  ```

---

## 2. Prerequisites Checklist for Any Device

Before running, confirm your friend has these installed:

1. **Python 3.10 or 3.11 (64-bit)**
   - Check version in terminal:
     ```bash
     python --version
     # or on Mac/Linux:
     python3 --version
     ```
   - Must output: `Python 3.10.x` or `Python 3.11.x`.
   - *Windows note:* Make sure Python is added to the system `PATH`.
2. **Node.js (v18 or v20 LTS) & npm**
   - Check version:
     ```bash
     node -v
     npm -v
     ```
3. **Project Files Integrity**
   - Confirm that the `backend/models/` folder contains the pretrained files:
     - `xgb.joblib` (ML risk model)
     - `bn.pkl` (Bayesian Network DAG & CPTs)
     - `graph.graphml` (Austin road network graph)

---

## 3. Step-by-Step Clean Setup on a New Device

Follow these exact steps on your friend's laptop:

### Step 1: Remove Any Copied Virtual Environment
Open PowerShell or Command Prompt in the project folder and delete any inherited `.venv`:
```powershell
# Windows PowerShell
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue

# Or Windows Command Prompt (CMD)
rmdir /s /q .venv

# Or macOS / Linux
rm -rf .venv
```

---

### Step 2: Create a Fresh Python Virtual Environment
```bash
# Windows
python -m venv .venv

# macOS / Linux
python3 -m venv .venv
```

---

### Step 3: Activate the Virtual Environment
* **Windows PowerShell**:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
  *(If you get a script permission error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*
* **Windows Command Prompt (CMD)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
* **macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```

Your prompt will now show `(.venv)`.

---

### Step 4: Install Backend Dependencies
Upgrade `pip` and install all pinned packages:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```
*(This takes about 1–3 minutes to download and cache wheels).*

---

### Step 5: Verify the Backend Installation
Run database migrations and the automated test suite:
```bash
python backend/manage.py migrate
python backend/manage.py test api -v 2
```

**Expected verification output:**
```text
[SafeRoute AI] Pre-warming in-memory AI model singletons...
 -> XGBoost model loaded.
 -> Bayesian Network loaded.
 -> OpenStreetMap road graph loaded.
 -> Expert rule engine initialized.
[SafeRoute AI] All models successfully cached in memory.

Found 7 test(s).
...
Ran 7 tests in 0.180s
OK
```
If you see **OK**, the backend, models, and graph are 100% operational on this machine!

---

### Step 6: Install Frontend Dependencies
Open a terminal in the project root:
```bash
cd frontend
npm install
cd ..
```

---

## 4. How to Launch the Application

### Option A: The 1-Click Launchers (Easiest)

* **Windows Command Prompt**:
  Double-click `start.bat` or run:
  ```cmd
  start.bat
  ```
* **Windows PowerShell**:
  ```powershell
  .\start.ps1
  ```
* **macOS / Linux**:
  ```bash
  chmod +x start.sh
  ./start.sh
  ```

---

### Option B: Manual Two-Terminal Launch (Best for Debugging)

If anything behaves unexpectedly, running two separate terminals allows you to view both logs in real time:

#### Terminal 1 — Backend (Port 8000)
```powershell
# Activate venv if not activated
.\.venv\Scripts\activate
python backend/manage.py runserver 0.0.0.0:8000
```
*Verify in browser:* Open [http://127.0.0.1:8000/api/health/](http://127.0.0.1:8000/api/health/). It should return `{"status": "healthy"}`.

#### Terminal 2 — Frontend (Port 5173)
```powershell
cd frontend
npm run dev
```
*Open application:* Visit [http://localhost:5173](http://localhost:5173) in Chrome or Edge.

---

### Option C: Docker Compose (Zero Configuration Setup)

If your friend has **Docker Desktop** installed, they don't even need to install Python or Node:
```bash
docker compose up --build
```
* Access frontend at: [http://localhost:5173](http://localhost:5173)
* Access backend API at: [http://localhost:8000](http://localhost:8000)

---

## 5. Troubleshooting Matrix (Common Errors & Fixes)

| Error Message / Symptom | Root Cause | Solution |
| :--- | :--- | :--- |
| `Fatal error in launcher: Unable to create process using '...'` | `.venv` was copied from another machine with hardcoded file paths. | Delete `.venv` (`rmdir /s /q .venv`) and run `python -m venv .venv` followed by `pip install -r requirements.txt`. |
| `ModuleNotFoundError: No module named 'django'` (or `xgboost`, `pgmpy`) | Running system Python instead of the activated virtual environment, or `pip install` was skipped. | Run `.\.venv\Scripts\activate` first, then run `pip install -r requirements.txt`. |
| `File start.ps1 cannot be loaded because running scripts is disabled` | Windows PowerShell ExecutionPolicy is set to Restricted. | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in the PowerShell window, or simply double-click `start.bat`. |
| `Error: That port is already in use (8000)` | A previous Django instance or another app is occupying port 8000. | In PowerShell: `Get-Process python* \| Stop-Process -Force` (or kill the process using port 8000 via Task Manager). |
| `Failed to fetch` or `Network Error` in UI | The React frontend is running, but the Django backend is offline. | Start the backend in Terminal 1 with `python backend/manage.py runserver 0.0.0.0:8000`. Test [http://127.0.0.1:8000/api/health/](http://127.0.0.1:8000/api/health/). |
| `Microsoft Visual C++ 14.0 or greater is required` during `pip install` | Device is running Python 3.12 or 3.13, which lacks pre-built wheels for older spatial libraries. | Uninstall Python 3.12/3.13 and install **Python 3.11.x** (64-bit) from python.org. |
| `npm ERR! code ENOENT` / `vite not found` | Frontend dependencies have not been installed. | Navigate to `frontend/` and run `npm install`. |
| `FileNotFoundError: models/xgb.joblib` | Model files were accidentally deleted or not copied in the transfer. | Verify that `backend/models/xgb.joblib`, `bn.pkl`, and `graph.graphml` are present in the folder. |

---

## 6. How to Share the Project Properly with Teammates

When sharing this project via ZIP or Google Drive:

1. **DO NOT include**:
   - ❌ `.venv/` (contains hundreds of MB of machine-specific binary stubs)
   - ❌ `frontend/node_modules/` (contains thousands of machine-specific Node modules)
   - ❌ `backend/db.sqlite3` (auto-generated on `migrate`)
   - ❌ Large raw datasets (`US_Accidents_March23.csv` — over 3 GB)
2. **DO include**:
   - ✅ `backend/` (all code and `backend/models/`)
   - ✅ `frontend/` (src, public, package.json, vite.config.ts)
   - ✅ `requirements.txt`
   - ✅ `start.bat`, `start.ps1`, `start.sh`
   - ✅ `SETUP_INSTRUCTIONS.md`

By following this clean setup, the project will run smoothly on any teammate or evaluator machine.
