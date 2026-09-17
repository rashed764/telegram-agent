import os
import logging
import asyncio
import random
from typing import List, Dict, Any, Optional
from telethon import TelegramClient
from telethon.errors import FloodWaitError, AuthKeyError, SessionPasswordNeededError
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class TelegramScout:
    def __init__(self, api_id: Optional[int] = None, api_hash: Optional[str] = None, session_name: str = "scout_session"):
        raw_api_id = api_id if api_id is not None else os.getenv("TELEGRAM_API_ID", "0")
        try:
            self.api_id = int(raw_api_id)
        except (ValueError, TypeError):
            self.api_id = 0

        self.api_hash = api_hash if api_hash is not None else os.getenv("TELEGRAM_API_HASH", "")
        self.session_name = session_name
        self._client: Optional[TelegramClient] = None

    def get_client(self) -> TelegramClient:
        if not self._client:
            if not self.api_id or not self.api_hash or self.api_id == 0:
                logger.warning("Telegram API ID or Hash not configured properly. Running in offline/mock mode.")
            self._client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        return self._client

    async def _ensure_connected(self, client: TelegramClient):
        try:
            is_conn = client.is_connected()
            if asyncio.iscoroutine(is_conn):
                is_conn = await is_conn
            if not is_conn:
                await client.connect()
        except (AuthKeyError, SessionPasswordNeededError) as auth_err:
            logger.error(f"Telegram authentication/session error: {auth_err}")
            raise ConnectionError(f"Telegram session authorization failed: {auth_err}")
        except Exception as conn_err:
            logger.warning(f"Client connection warning (expected if offline/mocked): {conn_err}")

    async def search_messages(self, entity: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        client = self.get_client()
        results = []
        max_retries = 3

        for attempt in range(max_retries):
            try:
                await self._ensure_connected(client)
                
                delay = random.uniform(1.0, 3.0)
                await asyncio.sleep(delay)

                async for message in client.iter_messages(entity, search=query, limit=limit):
                    file_info = None
                    if message.file:
                        file_info = {
                            "name": getattr(message.file, "name", None) or f"file_{message.id}",
                            "size": getattr(message.file, "size", 0),
                            "mime_type": getattr(message.file, "mime_type", "application/octet-stream"),
                            "ext": getattr(message.file, "ext", "")
                        }

                    results.append({
                        "message_id": message.id,
                        "date": str(message.date) if message.date else "",
                        "text": message.text or "",
                        "sender_id": getattr(message, "sender_id", None),
                        "file": file_info
                    })
                break
            except FloodWaitError as fwe:
                wait_time = fwe.seconds
                logger.warning(f"Telegram FloodWaitError encountered during search_messages. Sleeping for {wait_time}s (attempt {attempt+1}/{max_retries})...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"Error searching messages in entity {entity} with query '{query}': {e}")
                break
        
        return results

    async def get_message_file_metadata(self, entity: str, message_id: int) -> Optional[Dict[str, Any]]:
        client = self.get_client()
        max_retries = 3

        for attempt in range(max_retries):
            try:
                await self._ensure_connected(client)

                delay = random.uniform(1.0, 3.0)
                await asyncio.sleep(delay)

                messages = await client.get_messages(entity, ids=message_id)
                if messages:
                    msg = messages if not isinstance(messages, list) else messages[0]
                    if msg and msg.file:
                        return {
                            "message_id": msg.id,
                            "name": getattr(msg.file, "name", None) or f"file_{msg.id}",
                            "size": getattr(msg.file, "size", 0),
                            "mime_type": getattr(msg.file, "mime_type", "application/octet-stream"),
                            "ext": getattr(msg.file, "ext", "")
                        }
                break
            except FloodWaitError as fwe:
                wait_time = fwe.seconds
                logger.warning(f"Telegram FloodWaitError encountered during get_message_file_metadata. Sleeping for {wait_time}s (attempt {attempt+1}/{max_retries})...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"Failed to get message file metadata for {entity} msg {message_id}: {e}")
                break
        return None
