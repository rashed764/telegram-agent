import os
import logging
import time
from typing import List, Callable, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class GeminiKeyPool:

    def __init__(self):
        self.keys: List[str] = []
        self.key_status = {}  # key -> {"status": "active" | "exhausted" | "invalid", "cooldown_until": float}
        self.current_index = 0
        self._load_keys()

    def _load_keys(self):
        for i in range(1, 9):
            key = os.getenv(f"GEMINI_API_KEY_{i}")
            if key and not key.startswith("your_"):
                self.keys.append(key)
                self.key_status[key] = {"status": "active", "cooldown_until": 0.0}
        
        # Fallback if no numbered keys found, try GEMINI_API_KEY
        if not self.keys:
            single_key = os.getenv("GEMINI_API_KEY")
            if single_key and not single_key.startswith("your_"):
                self.keys.append(single_key)
                self.key_status[single_key] = {"status": "active", "cooldown_until": 0.0}

        logger.info(f"Initialized GeminiKeyPool with {len(self.keys)} active keys.")

    def get_next_key(self) -> str:
        """Get the next available active key using round-robin rotation."""
        if not self.keys:
            raise ValueError("No Gemini API keys available in pool.")

        now = time.time()
        attempts = 0
        while attempts < len(self.keys):
            key = self.keys[self.current_index]
            info = self.key_status[key]
            
            # Check if exhausted cooldown has expired
            if info["status"] == "exhausted" and now >= info["cooldown_until"]:
                info["status"] = "active"

            if info["status"] == "active":
                # Advance index for next call
                self.current_index = (self.current_index + 1) % len(self.keys)
                return key

            self.current_index = (self.current_index + 1) % len(self.keys)
            attempts += 1

        # If all keys are exhausted/invalid, reset exhausted keys to give them another try or raise error
        logger.warning("All Gemini API keys are currently exhausted/invalid. Resetting exhausted keys cooldown.")
        for key, info in self.key_status.items():
            if info["status"] == "exhausted":
                info["status"] = "active"
                info["cooldown_until"] = 0.0

        if self.keys:
            key = self.keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.keys)
            return key

        raise ValueError("All Gemini API keys are invalid or exhausted.")

    def mark_key_status(self, key: str, status: str, cooldown: float = 60.0):
        """Mark a key status as 'active', 'exhausted', or 'invalid'."""
        if key in self.key_status:
            self.key_status[key]["status"] = status
            if status == "exhausted":
                self.key_status[key]["cooldown_until"] = time.time() + cooldown
            logger.warning(f"Gemini API key ending in ...{key[-4:] if len(key)>=4 else key} marked as {status}.")

    async def execute_with_rotation(self, api_call_func: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute an async API call function with automatic failover and key rotation on 429, 401, 403."""
        max_retries = max(1, len(self.keys))
        last_exception = None

        for attempt in range(max_retries):
            key = self.get_next_key()
            try:
                return await api_call_func(key, *args, **kwargs)
            except Exception as e:
                last_exception = e
                error_str = str(e)
                status_code = getattr(e, "status_code", None) or getattr(e, "code", None)

                # Detect 429, 401, 403 from status code or error message
                is_429 = status_code == 429 or "429" in error_str or "ResourceExhausted" in error_str or "rate limit" in error_str.lower()
                is_401 = status_code == 401 or "401" in error_str or "Unauthorized" in error_str
                is_403 = status_code == 403 or "403" in error_str or "Forbidden" in error_str

                if is_429:
                    self.mark_key_status(key, "exhausted", cooldown=30.0)
                elif is_401 or is_403:
                    self.mark_key_status(key, "invalid", cooldown=86400.0)
                else:
                    # Non-rotational error, re-raise immediately
                    raise e

                logger.info(f"Retrying with next Gemini API key (Attempt {attempt + 1}/{max_retries})...")

        raise last_exception
