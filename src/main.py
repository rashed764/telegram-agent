import asyncio
import logging
import os
import random
import html
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from dotenv import load_dotenv

# Load core modules
from src.core.rate_limiter import RateLimiterMiddleware
from src.core.agent_brain import AgentBrain
from src.core.safety import ContentSafetyFilter
from src.core.router import DeliveryRouter
from src.core.storage import StorageManager
from src.core.mcp_bridge import MCPBridge, inspect_figma_file
from src.tools.web_search import search_web
from src.tools.github_search import search_github_repositories, search_github_code
from src.tools.telegram_scout import TelegramScout
from src.database import init_db, upsert_user, log_search

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize singletons
brain = AgentBrain()
storage = StorageManager()
scout = TelegramScout()


async def start_handler(message: Message):
    """Handle /start command."""
    user_id = message.from_user.id if message.from_user else 0
    username = message.from_user.username if message.from_user else ""
    first_name = message.from_user.first_name if message.from_user else "Scout"
    
    try:
        await upsert_user(user_id, username, first_name)
    except Exception as db_err:
        logger.warning(f"Database upsert failed in start_handler (non-blocking): {db_err}")
    
    safe_name = html.escape(first_name)
    welcome_text = (
        f"👋 Hello, <b>{safe_name}</b>!\n\n"
        "Welcome to the <b>Telegram Autonomous File Scout AI Agent</b> 🤖📁\n"
        "I can help you search, analyze, download, and process files using Gemini intelligence and multi-tool workflows.\n\n"
        "Type /help to see available commands."
    )
    await message.answer(welcome_text, parse_mode="HTML")


async def help_handler(message: Message):
    """Handle /help command."""
    help_text = (
        "🤖 <b>Telegram Autonomous File Scout AI Agent — Help Menu</b>\n\n"
        "<b>Core Commands:</b>\n"
        "• /start - Initialize connection and welcome\n"
        "• /help - Display this help guide\n\n"
        "<b>Features:</b>\n"
        "• Send files or documents for Gemini AI scouting & analysis\n"
        "• Autonomous file organization & search\n"
        "• Multi-key Gemini rotation & failover\n"
    )
    await message.answer(help_text, parse_mode="HTML")


async def query_handler(message: Message):
    """Process user natural language text queries using the full agent lifecycle."""
    user_id = message.from_user.id if message.from_user else 0
    username = message.from_user.username if message.from_user else ""
    first_name = message.from_user.first_name if message.from_user else "Scout"
    
    try:
        await upsert_user(user_id, username, first_name)
    except Exception as db_err:
        logger.warning(f"Database upsert failed in query_handler (non-blocking): {db_err}")
    
    query = message.text
    logger.info(f"Received query from user {user_id}: '{query}'")
    
    status_msg = await message.answer("🔍 <b>Analyzing your request...</b>", parse_mode="HTML")
    
    try:
        brain_result = await brain.think(query)
        
        thought = brain_result.get("thought", "")
        plan = brain_result.get("plan", "")
        tool_call = brain_result.get("tool_call")
        response = brain_result.get("response", "")
        
        if isinstance(tool_call, dict) and "error" in tool_call:
            err_details = html.escape(str(tool_call.get("error", "Unknown CoT parse error")))
            await status_msg.edit_text(f"⚠️ <b>AI Reasoning Error:</b> The model generated an invalid tool request. Please try rephrasing your query.\n<code>{err_details}</code>", parse_mode="HTML")
            try:
                await log_search(user_id, query, status="COT_ERROR")
            except Exception as db_err:
                logger.warning(f"Database logging failed (non-blocking): {db_err}")
            return

        try:
            await log_search(user_id, query, status="PROCESSING")
        except Exception as db_err:
            logger.warning(f"Database logging failed (non-blocking): {db_err}")
        
        if tool_call and isinstance(tool_call, dict) and "name" in tool_call:
            tool_name = tool_call.get("name")
            args = tool_call.get("arguments", {}) or {}
            
            logger.info(f"Agent decided to invoke tool: '{tool_name}' with args: {args}")
            safe_tool_name = html.escape(str(tool_name))
            safe_plan = html.escape(str(plan))
            await status_msg.edit_text(f"🛰️ <b>Scouting with tool:</b> <code>{safe_tool_name}</code>...\n\n<i>Plan:</i> {safe_plan}", parse_mode="HTML")
            
            scout_results = None
            source_type = "web"
            
            try:
                if tool_name in ["mcp_serper_search", "search_web", "web_search"]:
                    q = args.get("query") or args.get("q") or query
                    scout_results = await MCPBridge.mcp_serper_search(q)
                    if not scout_results:
                        scout_results = search_web(q)
                    source_type = "web"

                elif tool_name in ["mcp_github_search", "search_github", "github_search"]:
                    q = args.get("query") or args.get("q") or query
                    scout_results = await MCPBridge.mcp_github_search(q)
                    if not scout_results:
                        scout_results = search_github_repositories(q)
                        if not scout_results:
                            scout_results = search_github_code(q)
                    source_type = "github"

                elif tool_name in ["mcp_figma_inspect", "inspect_figma"]:
                    file_key = args.get("file_key") or args.get("query") or "default_key"
                    figma_data = await MCPBridge.mcp_figma_inspect(file_key)
                    scout_results = [figma_data]
                    source_type = "web"

                elif tool_name in ["search_telegram", "telegram_scout"]:
                    entity = args.get("entity") or "@test_channel"
                    q = args.get("query") or args.get("q") or query
                    scout_results = await scout.search_messages(entity, q)
                    source_type = "telegram"
            except (ValueError, ConnectionError, Exception) as tool_err:
                logger.error(f"Tool execution error: {tool_err}")
                err_msg = str(tool_err)
                if "Telegram Search API credentials" in err_msg:
                    await status_msg.edit_text("❌ <b>Error:</b> Telegram Search API credentials are not set correctly.\nটেলিগ্রাম সার্চ এপিআই ক্রেডেনশিয়াল সঠিকভাবে সেট করা হয়নি।", parse_mode="HTML")
                else:
                    await status_msg.edit_text(f"❌ <b>Tool Error:</b> <code>{html.escape(err_msg)}</code>", parse_mode="HTML")
                return
            
            if not scout_results:
                await status_msg.edit_text("❌ No files, code, or links were found for this query.", parse_mode="HTML")
                try:
                    await log_search(user_id, query, status="NO_RESULTS")
                except Exception as db_err:
                    logger.warning(f"Database logging failed (non-blocking): {db_err}")
                return
            
            candidate = scout_results[0]
            url = candidate.get("url") or candidate.get("html_url") or candidate.get("raw_url") or candidate.get("thumbnail_url")
            file_name = candidate.get("name") or candidate.get("title") or "downloaded_file"
            file_size = candidate.get("size") or candidate.get("file", {}).get("size") if isinstance(candidate.get("file"), dict) else 0
            
            if url:
                safety_check = ContentSafetyFilter.is_safe_url(url)
                if not safety_check["is_safe"]:
                    safe_reason = html.escape(safety_check['reason'])
                    await status_msg.edit_text(f"⚠️ <b>Content Safety Blocked:</b>\n{safe_reason}", parse_mode="HTML")
                    try:
                        await log_search(user_id, query, status="BLOCKED")
                    except Exception as db_err:
                        logger.warning(f"Database logging failed (non-blocking): {db_err}")
                    return
            
            if file_name:
                safety_check = ContentSafetyFilter.is_safe_file(file_name)
                if not safety_check["is_safe"]:
                    safe_reason = html.escape(safety_check['reason'])
                    await status_msg.edit_text(f"⚠️ <b>Content Safety Blocked:</b>\n{safe_reason}", parse_mode="HTML")
                    try:
                        await log_search(user_id, query, status="BLOCKED")
                    except Exception as db_err:
                        logger.warning(f"Database logging failed (non-blocking): {db_err}")
                    return

            route_plan = DeliveryRouter.route_item(
                source_type=source_type,
                file_size=file_size,
                url=url,
                file_name=file_name
            )
            
            route = route_plan["route"]
            action_details = route_plan["action_details"]
            warning = route_plan["warning"]
            
            if route == "stage_upload" and url and not url.endswith(".png"):
                await status_msg.edit_text(f"📥 <b>Staging & downloading file...</b>", parse_mode="HTML")
                try:
                    downloaded = storage.download_file(url, filename=file_name)
                    file_path = downloaded["file_path"]
                    
                    await status_msg.edit_text(f"📤 <b>Uploading file to Telegram...</b>", parse_mode="HTML")
                    safe_file_name = html.escape(str(file_name))
                    await message.answer_document(
                        document=FSInputFile(file_path),
                        caption=f"📁 <b>Scouted File:</b> <code>{safe_file_name}</code>\n\n🤖 Powered by Telegram Scout AI Agent.",
                        parse_mode="HTML"
                    )
                    await status_msg.delete()
                    
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as dl_err:
                    logger.error(f"Failed to stage file: {dl_err}")
                    safe_err = html.escape(str(dl_err))
                    await status_msg.edit_text(f"❌ Failed to download and upload staged file: <code>{safe_err}</code>", parse_mode="HTML")
            
            elif route == "direct_link" and url:
                safe_file_name = html.escape(str(file_name))
                safe_url = html.escape(str(url))
                safe_action = html.escape(str(action_details))
                html_link = f"🔗 <b>Scouted Link Discovery:</b> <a href=\"{safe_url}\">{safe_file_name}</a>\n\n<i>Action:</i> {safe_action}"
                if warning:
                    safe_warning = html.escape(str(warning))
                    html_link += f"\n\n⚠️ <b>Notice:</b> {safe_warning}"
                await status_msg.edit_text(html_link, parse_mode="HTML", disable_web_page_preview=True)
                
            else:
                final_text = response or f"Processed complete search via <code>{html.escape(str(tool_name))}</code> successfully."
                await status_msg.edit_text(f"ℹ️ <b>Scouting Complete:</b>\n\n{html.escape(str(final_text))}", parse_mode="HTML")
            
            try:
                await log_search(user_id, query, status="SUCCESS")
            except Exception as db_err:
                logger.warning(f"Database logging failed (non-blocking): {db_err}")
        
        else:
            clean_resp = response or "Hello! I am your Telegram Autonomous File Scout AI Agent. How can I help you search, scout, or analyze files today?"
            await status_msg.edit_text(html.escape(str(clean_resp)), parse_mode="HTML")
            try:
                await log_search(user_id, query, status="SUCCESS")
            except Exception as db_err:
                logger.warning(f"Database logging failed (non-blocking): {db_err}")

    except Exception as e:
        logger.exception(f"Error executing query flow: {e}")
        safe_err = html.escape(str(e))
        await status_msg.edit_text(f"❌ <b>An error occurred while scouting:</b>\n<code>{safe_err}</code>", parse_mode="HTML")
        try:
            await log_search(user_id, query, status="FAILED")
        except Exception as db_err:
            logger.warning(f"Database logging failed (non-blocking): {db_err}")


async def main():
    if not BOT_TOKEN or BOT_TOKEN == "your_telegram_bot_token_here":
        logger.error("TELEGRAM_BOT_TOKEN is not configured in .env!")
        print("[ERROR] TELEGRAM_BOT_TOKEN is missing or invalid in .env")
        return

    try:
        await init_db()
    except Exception as db_err:
        logger.error(f"Failed to initialize SQLite database at start: {db_err}")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.message.middleware(RateLimiterMiddleware(rate_limit_seconds=2.0))

    dp.message.register(start_handler, Command("start"))
    dp.message.register(help_handler, Command("help"))
    dp.message.register(query_handler, F.text & ~F.text.startswith("/"))

    logger.info("Starting Telegram Autonomous File Scout AI Agent (Long Polling)...")
    try:
        await asyncio.sleep(2)
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.exception(f"Polling error: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user.")
