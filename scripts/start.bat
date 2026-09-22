@echo off
REM scripts\start.bat — launch Synapse daemon + Tauri UI concurrently.
REM Prerequisites: scripts\setup_env.bat has been run, .env keys are set.
REM Verify first with: python -m core.doctor
cd /d "%~dp0.."
echo [1/2] Starting Python daemon on :8420 ...
start "Synapse Daemon" cmd /k ".venv\Scripts\activate && python core/server.py"
echo [2/2] Starting Tauri UI (http://localhost:1420) ...
start "Synapse UI" cmd /k "cd app && npm run tauri dev"
echo Both windows launched. Trigger a card with Ctrl+Shift+Space (once registered)
echo or: Invoke-RestMethod -Method Post http://127.0.0.1:8420/invoke -ContentType "application/json" -Body '{"query":"ping"}'
