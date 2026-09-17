import time
import logging
from typing import Dict, Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message

logger = logging.getLogger(__name__)


class RateLimiterMiddleware(BaseMiddleware):
    """
    Aiogram middleware implementing per-user request rate-limiting / throttling
    to prevent flooding (default: 1 message per 2 seconds).
    """

    def __init__(self, rate_limit_seconds: float = 2.0):
        super().__init__()
        self.rate_limit_seconds = rate_limit_seconds
        self.user_timestamps: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        current_time = time.time()
        last_time = self.user_timestamps.get(user_id, 0.0)

        if current_time - last_time < self.rate_limit_seconds:
            warning_text = "⚠️ Please wait a moment before sending another request."
            logger.warning(f"Rate limit exceeded for user {user_id}. Throttling request.")
            try:
                await event.answer(warning_text)
            except Exception as e:
                logger.error(f"Failed to send rate-limit warning: {e}")
            return  # Block handler execution

        self.user_timestamps[user_id] = current_time
        return await handler(event, data)
