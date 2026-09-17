import sys
import os
from dotenv import load_dotenv

def test_imports():
    print("Testing Python environment and imports...")
    
    # Load .env
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
    
    imports = {
        "aiogram": False,
        "dotenv": False,
        "pydantic": False,
        "aiofiles": False,
        "aiosqlite": False,
        "google_genai": False,
        "langchain_google_genai": False
    }
    
    try:
        import aiogram
        imports["aiogram"] = True
        print(f"  [OK] aiogram version: {aiogram.__version__}")
    except ImportError as e:
        print(f"  [FAIL] aiogram: {e}")
        
    try:
        import dotenv
        imports["dotenv"] = True
        print(f"  [OK] python-dotenv loaded")
    except ImportError as e:
        print(f"  [FAIL] python-dotenv: {e}")

    try:
        import pydantic
        imports["pydantic"] = True
        print(f"  [OK] pydantic version: {pydantic.__version__}")
    except ImportError as e:
        print(f"  [FAIL] pydantic: {e}")

    try:
        import aiofiles
        imports["aiofiles"] = True
        print(f"  [OK] aiofiles loaded")
    except ImportError as e:
        print(f"  [FAIL] aiofiles: {e}")

    try:
        import aiosqlite
        imports["aiosqlite"] = True
        print(f"  [OK] aiosqlite loaded")
    except ImportError as e:
        print(f"  [FAIL] aiosqlite: {e}")

    try:
        import google.genai
        imports["google_genai"] = True
        print(f"  [OK] google-genai loaded")
    except ImportError as e:
        print(f"  [WARN] google-genai: {e}")

    try:
        import langchain_google_genai
        imports["langchain_google_genai"] = True
        print(f"  [OK] langchain-google-genai loaded")
    except ImportError as e:
        print(f"  [WARN] langchain_google_genai: {e}")

    # Check env variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    print(f"  [INFO] TELEGRAM_BOT_TOKEN present: {bool(bot_token)}")
    
    gemini_keys = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 9)]
    valid_keys = sum(1 for k in gemini_keys if k and not k.startswith("your_"))
    print(f"  [INFO] Valid Gemini API keys configured: {valid_keys}/8")

if __name__ == "__main__":
    test_imports()
