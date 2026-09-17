import unittest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram.types import Message, User

from src.core.rate_limiter import RateLimiterMiddleware
from src.tools.telegram_scout import TelegramScout
from telethon.errors import FloodWaitError


class TestRateLimiterAndAntiFlood(unittest.TestCase):

    def test_rate_limiter_middleware_throttling(self):
        async def run_test():
            middleware = RateLimiterMiddleware(rate_limit_seconds=2.0)
            handler_mock = AsyncMock(return_value="success")

            user1 = User(id=101, is_bot=False, first_name="Alice")
            message1 = AsyncMock(spec=Message)
            message1.from_user = user1
            message1.answer = AsyncMock()

            # First request should succeed
            res1 = await middleware(handler_mock, message1, {})
            self.assertEqual(res1, "success")
            handler_mock.assert_awaited_once()

            # Immediate second request should be throttled
            handler_mock.reset_mock()
            res2 = await middleware(handler_mock, message1, {})
            self.assertIsNone(res2)
            handler_mock.assert_not_awaited()
            message1.answer.assert_awaited_once()
            args, _ = message1.answer.call_args
            self.assertIn("Please wait a moment", args[0])

            # Different user should succeed immediately
            user2 = User(id=102, is_bot=False, first_name="Bob")
            message2 = AsyncMock(spec=Message)
            message2.from_user = user2
            message2.answer = AsyncMock()

            res3 = await middleware(handler_mock, message2, {})
            self.assertEqual(res3, "success")
            handler_mock.assert_awaited_once()

        asyncio.run(run_test())

    @patch("src.tools.telegram_scout.TelegramClient")
    def test_telegram_scout_flood_wait_retry(self, mock_client_cls):
        async def run_test():
            mock_client = AsyncMock()
            mock_client.is_connected.return_value = True

            call_count = 0
            async def mock_iter_messages(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise FloodWaitError(request=None, capture=1)
                return
                yield  # make it an async generator

            mock_client.iter_messages = mock_iter_messages
            mock_client_cls.return_value = mock_client

            scout = TelegramScout(api_id=123, api_hash="abc", session_name="test_session")
            scout._client = mock_client

            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                results = await scout.search_messages("@test_channel", "python", limit=5)
                self.assertEqual(results, [])
                # Verify sleep was called for FloodWait duration (1s) plus human-like delays
                self.assertTrue(mock_sleep.awaited)
                self.assertEqual(call_count, 2)

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
