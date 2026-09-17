@echo off
title Telegram Autonomous File Scout AI Agent
echo Starting Telegram Autonomous File Scout AI Agent...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment 'venv' not found. Running with global python.
)
set PYTHONPATH=%CD%
python -m src.main
pause
