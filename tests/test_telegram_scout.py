import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from src.tools.telegram_scout import TelegramScout


class TestTelegramScout(unittest.TestCase):

    def test_search_messages_mocked(self):
        async def run():
            scout = TelegramScout(api_id=12345, api_hash="mock_hash")
            
            # Mock TelethonClient
            mock_client = AsyncMock()
            mock_client.is_connected.return_value = True

            # Mock message object
            mock_msg = MagicMock()
            mock_msg.id = 101
            mock_msg.date = "2026-09-16 12:00:00"
            mock_msg.text = "Here is the archive.zip file"
            mock_msg.sender_id = 98765
            
            # Mock file object
            mock_file = MagicMock()
            mock_file.name = "archive.zip"
            mock_file.size = 2048
            mock_file.mime_type = "application/zip"
            mock_file.ext = ".zip"
            mock_msg.file = mock_file

            # Async generator for iter_messages
            async def mock_iter_messages(*args, **kwargs):
                yield mock_msg

            mock_client.iter_messages = mock_iter_messages
            scout._client = mock_client

            results = await scout.search_messages("@test_channel", "archive")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["message_id"], 101)
            self.assertEqual(results[0]["text"], "Here is the archive.zip file")
            self.assertIsNotNone(results[0]["file"])
            self.assertEqual(results[0]["file"]["name"], "archive.zip")
            self.assertEqual(results[0]["file"]["size"], 2048)

        asyncio.run(run())

    def test_get_message_file_metadata_mocked(self):
        async def run():
            scout = TelegramScout(api_id=12345, api_hash="mock_hash")
            
            mock_client = AsyncMock()
            mock_client.is_connected.return_value = True

            mock_msg = MagicMock()
            mock_msg.id = 102
            mock_file = MagicMock()
            mock_file.name = "document.pdf"
            mock_file.size = 5120
            mock_file.mime_type = "application/pdf"
            mock_file.ext = ".pdf"
            mock_msg.file = mock_file

            mock_client.get_messages.return_value = mock_msg
            scout._client = mock_client

            metadata = await scout.get_message_file_metadata("@test_channel", 102)
            self.assertIsNotNone(metadata)
            self.assertEqual(metadata["message_id"], 102)
            self.assertEqual(metadata["name"], "document.pdf")
            self.assertEqual(metadata["size"], 5120)
            self.assertEqual(metadata["mime_type"], "application/pdf")

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
