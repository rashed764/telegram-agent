import os
from dotenv import load_dotenv

load_dotenv()

print("="*50)
print("TELEGRAM AUTONOMOUS FILE SCOUT - ENVIRONMENT & IMPORT VERIFICATION")
print("="*50)

try:
    import aiogram
    print(f"[SUCCESS] aiogram imported successfully (version: {aiogram.__version__})")
except Exception as e:
    print(f"[ERROR] Failed to import aiogram: {e}")

try:
    import dotenv
    print(f"[SUCCESS] python-dotenv imported successfully")
except Exception as e:
    print(f"[ERROR] Failed to import dotenv: {e}")

try:
    import google.genai
    print(f"[SUCCESS] google-genai imported successfully")
except Exception as e:
    print(f"[ERROR] Failed to import google-genai: {e}")

try:
    import pydantic
    print(f"[SUCCESS] pydantic imported successfully (version: {pydantic.__version__})")
except Exception as e:
    print(f"[ERROR] Failed to import pydantic: {e}")

# Check env variables
token = os.getenv("TELEGRAM_BOT_TOKEN")
has_token = bool(token and token != "your_telegram_bot_token_here")
print(f"TELEGRAM_BOT_TOKEN configured: {has_token}")

valid_gemini_count = 0
for i in range(1, 9):
    key = os.getenv(f"GEMINI_API_KEY_{i}")
    is_valid = bool(key and not key.startswith("your_"))
    if is_valid:
        valid_gemini_count += 1
    print(f"GEMINI_API_KEY_{i} configured: {is_valid}")

print(f"Total valid Gemini API keys: {valid_gemini_count}/8")
print("="*50)
print("Verification complete!")
