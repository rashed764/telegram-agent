import os
import sys
import asyncio
from pathlib import Path

# Ensure the root directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.web_search import search_web
from src.tools.github_search import search_github_repositories
from src.tools.telegram_scout import TelegramScout

async def test_search_web():
    print("Testing search_web...")
    try:
        # DDG HTML search fallback check
        results = search_web("python programming", num_results=2)
        print(f"search_web Results: {results}")
        if results:
            print("search_web: PASS")
            return "PASS"
        else:
            print("search_web: FAIL (Empty Results)")
            return "FAIL"
    except Exception as e:
        print(f"search_web: FAIL with Exception: {e}")
        return f"FAIL: {e}"

async def test_search_github():
    print("\nTesting search_github...")
    try:
        results = search_github_repositories("python template", per_page=2)
        print(f"search_github Results: {results}")
        if results:
            print("search_github: PASS")
            return "PASS"
        else:
            print("search_github: FAIL (Empty Results)")
            return "FAIL"
    except Exception as e:
        print(f"search_github: FAIL with Exception: {e}")
        return f"FAIL: {e}"

async def test_search_telegram():
    print("\nTesting search_telegram...")
    session_file = Path("scout_session.session")
    print(f"Checking scout_session.session exists: {session_file.exists()}")
    
    scout = TelegramScout()
    try:
        client = scout.get_client()
        # Non-blocking connection check
        is_connected = client.is_connected()
        if asyncio.iscoroutine(is_connected):
            is_connected = await is_connected
        
        # We don't need to actually connect to Telegram in a test if it requires phone verification, 
        # but let's see if client can be retrieved and connects without crashing
        print(f"Telethon client configured. Connected: {is_connected}")
        print("search_telegram: PASS (Client instantiated)")
        return "PASS"
    except Exception as e:
        print(f"search_telegram: FAIL with Exception: {e}")
        return f"FAIL: {e}"

def test_storage():
    print("\nTesting storage...")
    download_dir = Path("data/downloads")
    try:
        download_dir.mkdir(parents=True, exist_ok=True)
        test_file = download_dir / "test_write.txt"
        test_file.write_text("write test")
        test_file.unlink()
        print("storage: PASS")
        return "PASS"
    except Exception as e:
        print(f"storage: FAIL with Exception: {e}")
        return f"FAIL: {e}"

async def main():
    from dotenv import load_dotenv
    load_dotenv()
    
    web_status = await test_search_web()
    github_status = await test_search_github()
    telegram_status = await test_search_telegram()
    storage_status = test_storage()
    
    print("\n=== CONNECTIVITY STATUS SUMMARY ===")
    print(f"search_web: {web_status}")
    print(f"search_github: {github_status}")
    print(f"search_telegram: {telegram_status}")
    print(f"storage: {storage_status}")

if __name__ == "__main__":
    asyncio.run(main())
