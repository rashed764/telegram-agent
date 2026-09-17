# Telegram Agent Deployment & Auto-Start Guide

This directory contains production deployment configurations and auto-start scripts for Linux (`systemd`), Windows (`Batch / Task Scheduler`), and Docker (`Docker Compose`).

---

## 1. Linux Systemd Service Setup

To run the Telegram Autonomous File Scout AI Agent as a persistent system service on Linux:

1. Copy or symlink `deploy/telegram_agent.service` to `/etc/systemd/system/telegram_agent.service`:
   ```bash
   sudo cp deploy/telegram_agent.service /etc/systemd/system/telegram_agent.service
   ```
2. Edit the service file if your installation path or user differs from `/opt/telegram_agent`:
   ```bash
   sudo nano /etc/systemd/system/telegram_agent.service
   ```
3. Reload systemd, enable, and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable telegram_agent.service
   sudo systemctl start telegram_agent.service
   ```
4. Check service status or view logs:
   ```bash
   sudo systemctl status telegram_agent.service
   sudo journalctl -u telegram_agent.service -f
   ```

---

## 2. Windows Auto-Start & Task Scheduler Setup

### Method A: Persistent Batch Wrapper Loop (`start_bot.bat`)
1. Double-click `deploy/start_bot.bat` or run it from command prompt. It will automatically run `src/main.py` using your virtual environment Python interpreter and restart it immediately if it crashes or stops.
2. To run it on Windows startup, place a shortcut of `start_bot.bat` into the Windows Startup folder (`shell:startup`).

### Method B: Windows Task Scheduler (XML / Task)
1. Open **Task Scheduler** (`taskschd.msc`).
2. Click **Create Task...**
3. **General**: Name it `TelegramAgentAutoStart`, set to run whether user is logged on or not with highest privileges.
4. **Triggers**: New trigger -> At startup.
5. **Actions**: New action -> Start a program:
   - Program/script: `C:\VS code\Telegram Agent\venv\Scripts\python.exe`
   - Add arguments: `src\main.py`
   - Start in: `C:\VS code\Telegram Agent\`
6. Click **OK** to save.

---

## 3. Docker & Docker Compose Deployment

To run the agent inside an isolated Docker container with automatic restart policy (`unless-stopped`):

1. Ensure your `.env` file is populated in the project root with `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEYS`, etc.
2. Build and run using Docker Compose:
   ```bash
   docker compose -f deploy/docker-compose.yml up -d --build
   ```
3. View container logs:
   ```bash
   docker compose -f deploy/docker-compose.yml logs -f
   ```
4. Stop container:
   ```bash
   docker compose -f deploy/docker-compose.yml down
   ```
