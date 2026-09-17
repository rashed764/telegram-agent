import asyncio
import unittest
from unittest.mock import AsyncMock
from aiogram.types import Message, User
from src.main import start_handler, help_handler


class TestBotHandlers(unittest.TestCase):

    def test_start_handler(self):
        async def run():
            message = AsyncMock(spec=Message)
            message.from_user = User(id=123, is_bot=False, first_name="TestUser")
            message.answer = AsyncMock()

            await start_handler(message)

            message.answer.assert_called_once()
            args, kwargs = message.answer.call_args
            self.assertIn("TestUser", args[0])
            self.assertEqual(kwargs.get("parse_mode"), "HTML")

        asyncio.run(run())

    def test_help_handler(self):
        async def run():
            message = AsyncMock(spec=Message)
            message.answer = AsyncMock()

            await help_handler(message)

            message.answer.assert_called_once()
            args, kwargs = message.answer.call_args
            self.assertIn("Help Menu", args[0])
            self.assertEqual(kwargs.get("parse_mode"), "HTML")

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
