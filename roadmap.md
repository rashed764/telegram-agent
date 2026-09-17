MASTER DEVELOPMENT ROADMAP

## 1. Architecture Overview
The Telegram Autonomous File Scout AI Agent is a local-server-hosted (Homelab/Local Machine) intelligent automation system.

- **Core Interface**: Telegram Bot (Aiogram using Long-Polling) running locally.
- **AI Brain & LLM Engine**: Powered by Google Gemini API using the **Gemini Lite Model** (`gemini-2.0-flash` or `gemini-1.5-flash`) for ultra-fast response times.
- **Resilient Multi-Key Pool**: A managed pool of ~8 Gemini API keys with automatic failover and key rotation triggered upon encountering HTTP status codes `429` (Rate Limit), `401` (Unauthorized), or `403` (Forbidden).
- **Built-in Reasoning Layer**: Integrated Chain of Thought (CoT) and structured prompt reasoning framework to ensure deep analytical planning, intent decomposition, and robust tool selection despite utilizing a high-speed lite model.
- **Scouting Layer**: Modular tools for Google Search, GitHub API, Web Scraping, and Telegram Userbot (Telethon) for cross-platform search.
- **Smart Delivery Engine**: Evaluates file size and source type to dynamically route delivery:
  - Direct Web Link for web discoveries.
  - Local Direct Upload (`bot.send_document`) for files under size threshold (e.g., <20MB) downloaded to local staging.
  - Telegram Message/File Forwarding (`client.forward_messages`) for items sourced from Telegram channels/groups.
- **Storage & Maintenance**: SQLite database for tracking, local temporary storage staging with automated background cleanup cron jobs.

## 2. Dependency Graph

```
[Phase 1: Foundation & Bot Core]
       │
       ▼
[Phase 2: Gemini Brain, Multi-Key Rotation & Scouting Tools]
       │
       ▼
[Phase 3: Smart Delivery & Local Storage Engine]
       │
       ▼
[Phase 4: Hardening, Integration & Final Verification]
```

## 3. Development Phases

### Phase 1: Foundation & Bot Core Setup
**Objective**: Establish the local python environment, configuration management, database, and basic Telegram long-polling bot skeleton.  
**Dependencies**: None  
**Verification Gate**: Bot successfully connects to Telegram, responds to `/start`, and logs interactions in SQLite.

- **Unit 1.1: Project Structure & Environment Setup**
  - **ID**: U-101
  - **Goal**: Initialize project directory structure, `requirements.txt`, and `.env` configuration template.
  - **Scope**: Create `src/`, `tests/`, `config/`, `data/` directories; set up `.env` template supporting multiple Gemini API keys (`GEMINI_API_KEY_1` to `GEMINI_API_KEY_8`) and Telegram bot token.
  - **Dependencies**: None
  - **Expected Result**: Clean workspace with python virtual environment and installed core dependencies (`aiogram`, `google-genai` / `langchain-google-genai`, `python-dotenv`, `pydantic`).
  - **Verification**: Run `python -c "import aiogram; print('OK')"` and verify environment variables load correctly.

- **Unit 1.2: Telegram Long-Polling Bot Initialization**
  - **ID**: U-102
  - **Goal**: Set up the basic Aiogram bot dispatcher using Long Polling to avoid webhook/public IP requirements on the local server.
  - **Scope**: Implement main bot entry point (`main.py`), basic command handlers (`/start`, `/help`).
  - **Dependencies**: U-101
  - **Expected Result**: Bot starts locally and responds to `/start` on Telegram.
  - **Verification**: Send `/start` to the bot in Telegram and receive a greeting response.

- **Unit 1.3: Database & Session Management**
  - **ID**: U-103
  - **Goal**: Initialize SQLite database for logging user queries, search history, and temporary state.
  - **Scope**: Create SQLAlchemy or aiosqlite models for users, search history, and cached file references.
  - **Dependencies**: U-102
  - **Expected Result**: SQLite database file (`bot.db`) created with tables for users and logs.
  - **Verification**: Verify table creation via sqlite3 CLI and successful write/read test on bot startup.

**Phase 1 Verification Gate**: Bot runs locally via long-polling, handles `/start`, and logs sessions to SQLite.

---

### Phase 2: Gemini Brain, Multi-Key Rotation & Scouting Tools
**Objective**: Implement the Gemini Lite model client, automated 8-key rotation/failover pool (`429`, `401`, `403`), Chain of Thought reasoning layer, and connect scouting tools for Web, GitHub, and Telegram.  
**Dependencies**: Phase 1  
**Verification Gate**: AI agent correctly handles key rotation upon rate-limits/auth errors, executes structured reasoning with the lite model, and invokes appropriate search tools returning raw data.

- **Unit 2.1: Gemini Multi-Key Pool & Rotation Manager**
  - **ID**: U-201
  - **Goal**: Implement an API key manager supporting ~8 Gemini API keys with automatic failover and rotation upon encountering `429` (Rate Limit), `401` (Unauthorized), or `403` (Forbidden) HTTP status codes.
  - **Scope**: Create `core/gemini_pool.py` to cycle through active keys, mark exhausted/invalid keys temporarily or permanently, and retry failed requests seamlessly without crashing the agent.
  - **Dependencies**: U-103
  - **Expected Result**: Resilient client wrapper that transparently switches API keys upon error detection.
  - **Verification**: Unit test mock responses returning 429/401/403 and verify that the manager rotates to the next available key and retries successfully.

- **Unit 2.2: Gemini Lite Model & Reasoning (CoT) Layer**
  - **ID**: U-202
  - **Goal**: Configure the Gemini Lite model (`gemini-2.0-flash` / `gemini-1.5-flash`) and integrate a Chain of Thought (CoT) reasoning prompt structure for agent decision making.
  - **Scope**: Create `core/agent_brain.py` incorporating system prompts requiring step-by-step reasoning (`<thought>`, `<plan>`, `<tool_call>`) prior to tool execution, ensuring high intelligence output from the lite model.
  - **Dependencies**: U-201
  - **Expected Result**: Agent successfully decomposes user queries using structured reasoning and produces valid tool selection payloads.
  - **Verification**: Test prompt inputs and verify output contains valid reasoning steps followed by correct tool invocation JSON.

- **Unit 2.3: Web & Google Search Tool**
  - **ID**: U-203
  - **Goal**: Implement Google Custom Search / SerpAPI tool and BeautifulSoup web scraper for direct link discovery.
  - **Scope**: Create `tools/web_search.py` returning top relevant URLs and document links.
  - **Dependencies**: U-202
  - **Expected Result**: Function searches the web and returns structured list of titles, URLs, and descriptions.
  - **Verification**: Execute search query via test script and verify returned valid URL list.

- **Unit 2.4: GitHub Search Tool**
  - **ID**: U-204
  - **Goal**: Implement GitHub API integration to search repositories, raw code files, and releases.
  - **Scope**: Create `tools/github_search.py` using GitHub REST API search endpoints.
  - **Dependencies**: U-202
  - **Expected Result**: Returns matching GitHub repository links, raw file URLs, and release assets.
  - **Verification**: Search for a known repository/file and verify correct GitHub raw links returned.

- **Unit 2.5: Telegram Scout & Userbot Integration**
  - **ID**: U-205
  - **Goal**: Set up Telethon/Pyrogram userbot client to search accessible public Telegram channels/groups for files.
  - **Scope**: Create `tools/telegram_scout.py` to search messages and retrieve file metadata/message IDs.
  - **Dependencies**: U-202
  - **Expected Result**: Userbot searches messages in configured channels/chats and returns message references.
  - **Verification**: Test telegram search query against a test chat and verify returned message object data.

**Phase 2 Verification Gate**: Gemini Lite agent successfully performs multi-key rotation on 429/401/403, executes reasoning CoT, and invokes Web, GitHub, and Telegram search tools.

---

### Phase 3: Smart Delivery & Local Storage Engine
**Objective**: Build the smart routing engine, local staging/caching mechanism, auto-cleanup worker, and content safety filter.  
**Dependencies**: Phase 2  
**Verification Gate**: Files are correctly evaluated by size and source, routed via Direct Link, Local Upload, or Telegram Forwarding, with auto-cleanup operational.

- **Unit 3.1: Smart Delivery Routing Engine**
  - **ID**: U-301
  - **Goal**: Implement decision logic to route results based on file size and source type.
  - **Scope**: Create `core/router.py`:
    - If direct web link → Send formatted markdown link with warning alert.
    - If file < 20MB & downloadable → Stage locally and prepare for upload.
    - If Telegram source → Prepare message/file forward.
  - **Dependencies**: U-2.x
  - **Expected Result**: Router correctly classifies candidate items into Link, Upload, or Forward actions.
  - **Verification**: Unit test router with mock file sizes and source types, verifying correct dispatch action.

- **Unit 3.2: Local Caching & Temporary Storage Manager**
  - **ID**: U-302
  - **Goal**: Implement local staging directory (`data/downloads/`) for handling files prior to upload.
  - **Scope**: Create file downloader utility with size checks and exception handling for oversized downloads.
  - **Dependencies**: U-301
  - **Expected Result**: Files successfully downloaded to local staging area with proper metadata logging.
  - **Verification**: Download test file via staging manager and verify presence in local directory.

- **Unit 3.3: Auto-Cleanup & Background Worker**
  - **ID**: U-303
  - **Goal**: Implement automated background cleanup (cron / async task) to delete temp files older than a specified duration (e.g., 1 hour).
  - **Scope**: Create `core/cleanup.py` utilizing background tasks or scheduled intervals to wipe staging directories.
  - **Dependencies**: U-302
  - **Expected Result**: Temporary files are automatically purged after expiration.
  - **Verification**: Run cleanup worker on a test directory with expired dummy files and verify deletion.

- **Unit 3.4: Content Safety & Moderation Filter**
  - **ID**: U-304
  - **Goal**: Implement guardrails and safety checks to screen URLs/files for malware signatures, explicit content flags, or malicious extensions.
  - **Scope**: Create `core/safety.py` to blacklist dangerous extensions (`.exe`, `.scr`, etc., if unauthorized) and scan URLs.
  - **Dependencies**: U-301
  - **Expected Result**: Malicious or forbidden items are filtered out before delivery.
  - **Verification**: Test filter with known safe vs. unsafe file types and verify blockage.

**Phase 3 Verification Gate**: Smart delivery router correctly executes links, uploads, and forwards; safety filter blocks hazards; auto-cleanup clears disk space.

---

### Phase 4: Hardening, Integration & Verification
**Objective**: Integrate all components into a seamless local bot execution flow, add rate-limiting/flood protection, and configure auto-start.  
**Dependencies**: Phase 3  
**Verification Gate**: End-to-end user query results in successful agent search, routing, delivery, and cleanup without crashing.

- **Unit 4.1: End-to-End Integration & Error Handling**
  - **ID**: U-401
  - **Goal**: Connect Telegram handlers, Gemini Agent Brain, Scouting Tools, and Smart Router into a cohesive message lifecycle flow.
  - **Scope**: Implement fallback error handling, user progress notifications ("Searching...", "Processing..."), and graceful exception recovery.
  - **Dependencies**: U-304
  - **Expected Result**: Bot handles user queries smoothly from prompt to delivery with informative status updates.
  - **Verification**: Send complex query via Telegram, observe step-by-step status messages and final correct file/link delivery.

- **Unit 4.2: Rate-Limiting, FloodWait Protection, & Delays**
  - **ID**: U-402
  - **Goal**: Implement behavioral delays and rate-limiting to prevent Telegram FloodWait errors during userbot scouting and forwarding.
  - **Scope**: Add randomized human-like delays (`asyncio.sleep`) between API calls and Telethon actions.
  - **Dependencies**: U-401
  - **Expected Result**: Zero Telegram API ban or FloodWait exceptions during multi-source scouting.
  - **Verification**: Simulate rapid consecutive user requests and verify throttling/delay behavior.

- **Unit 4.3: Systemd / Task Scheduler Auto-Start Setup**
  - **ID**: U-403
  - **Goal**: Configure local OS service (Systemd on Linux / Task Scheduler on Windows / Docker restart policy) to ensure the bot auto-starts on system boot.
  - **Scope**: Write systemd service file or Docker compose restart policy configuration.
  - **Dependencies**: U-402
  - **Expected Result**: Bot service automatically restarts on server reboot.
  - **Verification**: Reboot local environment test instance and verify bot reconnects and listens automatically.

**Phase 4 Verification Gate**: Fully operational local Telegram bot with robust error handling, anti-flood protection, and auto-restart capability.

## 4. Complete Execution Order

1. **U-101**: Project Structure & Environment Setup
2. **U-102**: Telegram Long-Polling Bot Initialization
3. **U-103**: Database & Session Management
4. **U-201**: Gemini Multi-Key Pool & Rotation Manager
5. **U-202**: Gemini Lite Model & Reasoning (CoT) Layer
6. **U-203**: Web & Google Search Tool
7. **U-204**: GitHub Search Tool
8. **U-205**: Telegram Scout & Userbot Integration
9. **U-301**: Smart Delivery Routing Engine
10. **U-302**: Local Caching & Temporary Storage Manager
11. **U-303**: Auto-Cleanup & Background Worker
12. **U-304**: Content Safety & Moderation Filter
13. **U-401**: End-to-End Integration & Error Handling
14. **U-402**: Rate-Limiting, FloodWait Protection, & Delays
15. **U-403**: Systemd / Task Scheduler Auto-Start Setup

## 5. Final Completion Gate
The project can only be declared 100% Complete when all the following criteria are met:

1. All 15 roadmap units are implemented, integrated, and verified.
2. The local Telegram bot successfully processes natural language prompts via Long Polling without requiring public IP or webhooks.
3. The Gemini API client successfully manages a pool of ~8 API keys with automatic failover and rotation upon encountering `429`, `401`, or `403` status codes.
4. The Gemini Lite model leverages built-in Chain of Thought (CoT) reasoning to accurately plan and invoke tools.
5. The Smart Delivery Engine correctly differentiates between Direct Links, Local Uploads (<20MB), and Telegram Forwards.
6. The Auto-Cleanup worker successfully purges temporary local files on schedule.
7. The system automatically restarts on server reboot via system service configuration.
