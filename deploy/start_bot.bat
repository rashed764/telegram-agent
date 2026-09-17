@echo off
TITLE Telegram Autonomous File Scout AI Agent - AutoRestart Wrapper
COLOR 0A

echo [INFO] Starting Telegram Agent in auto-restart loop...
cd /d "%~dp0"
cd ..

:loop
echo [%DATE% %TIME%] Launching Telegram Agent...
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe src\main.py
) else (
    python src\main.py
)

echo [%DATE% %TIME%] [WARNING] Telegram Agent stopped or crashed. Restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto loop
