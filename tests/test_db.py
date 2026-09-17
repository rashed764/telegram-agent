import asyncio
import os
import unittest
from src.database import init_db, upsert_user, log_search, cache_file_reference, get_user, get_search_logs

TEST_DB_PATH = os.path.join("data", "test_bot.db")


class TestDatabase(unittest.TestCase):

    def setUp(self):
        # Remove test db if exists
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def tearDown(self):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def test_database_operations(self):
        async def run():
            # 1. Initialize DB
            await init_db(TEST_DB_PATH)

            # 2. Test User Upsert and Read
            user_id = 999999
            await upsert_user(user_id, "testuser", "Test", TEST_DB_PATH)
            user = await get_user(user_id, TEST_DB_PATH)
            self.assertIsNotNone(user)
            self.assertEqual(user["username"], "testuser")
            self.assertEqual(user["first_name"], "Test")

            # 3. Test Search Log
            await log_search(user_id, "quantum computing papers", "SUCCESS", TEST_DB_PATH)
            logs = await get_search_logs(user_id, TEST_DB_PATH)
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0]["query"], "quantum computing papers")
            self.assertEqual(logs[0]["status"], "SUCCESS")

            # 4. Test File Caching
            await cache_file_reference("file_abc123", "/downloads/test.pdf", "telegram", None, TEST_DB_PATH)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
