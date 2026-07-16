@echo off
REM CareerPilot AI — Windows launcher
cd /d "%~dp0"
python -m agents.core.orchestrator
pause
