# scripts/setup_env.bat
# 1-click Windows developer setup for Synapse
# Run this from the repo root: scripts\setup_env.bat

@echo off
setlocal enabledelayedexpansion

echo.
echo  ╔══════════════════════════════════════╗
echo  ║     SYNAPSE — Developer Setup        ║
echo  ╚══════════════════════════════════════╝
echo.

:: ── Check Python ──────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.11+ from python.org
    pause & exit /b 1
)
echo [OK] Python found

:: ── Check Node ────────────────────────────────────────────────────────
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Install from nodejs.org
    pause & exit /b 1
)
echo [OK] Node.js found

:: ── Check Rust ────────────────────────────────────────────────────────
cargo --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Rust not found. Install from rustup.rs
    pause & exit /b 1
)
echo [OK] Rust/Cargo found

:: ── Python virtual env ────────────────────────────────────────────────
echo.
echo [1/4] Setting up Python virtual environment...
if not exist ".venv" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install --upgrade pip --quiet
pip install -r core\requirements.txt --quiet
echo [OK] Python dependencies installed

:: ── .env setup ────────────────────────────────────────────────────────
echo.
echo [2/4] Setting up environment...
if not exist ".env" (
    copy .env.example .env
    echo [!] .env created from template. Fill in your API keys in .env before running.
) else (
    echo [OK] .env already exists
)

:: ── Frontend dependencies ─────────────────────────────────────────────
echo.
echo [3/4] Installing frontend dependencies...
cd app
npm install --silent
cd ..
echo [OK] Node modules installed

:: ── Create notes directory ────────────────────────────────────────────
echo.
echo [4/4] Creating local data directories...
if not exist "%USERPROFILE%\synapse_notes" mkdir "%USERPROFILE%\synapse_notes"
if not exist "%USERPROFILE%\.synapse\logs" mkdir "%USERPROFILE%\.synapse\logs"
echo [OK] Directories created

:: ── Done ──────────────────────────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║  Setup complete!                                         ║
echo  ║                                                          ║
echo  ║  Next steps:                                             ║
echo  ║  1. Edit .env with your NEBIUS_API_KEY,                  ║
echo  ║     NEBIUS_PGVECTOR_URL, and TAVILY_API_KEY              ║
echo  ║  2. Terminal 1: python core/server.py                    ║
echo  ║  3. Terminal 2: cd app && npm run tauri dev              ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
pause
