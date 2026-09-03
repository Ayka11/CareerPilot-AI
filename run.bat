@echo off
cd /d "%~dp0"
echo ========================================
echo     CareerPilot AI - Starting...
echo ========================================

set PYTHONPATH=.
python app/main.py

echo.
echo CareerPilot AI run completed.
