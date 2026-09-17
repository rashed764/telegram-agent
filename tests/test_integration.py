import unittest
import tempfile
from pathlib import Path
from src.core.safety import ContentSafetyFilter
from src.core.router import DeliveryRouter
from src.database import init_db, upsert_user, log_search


class TestEndToEndIntegrationPipeline(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Use a temporary file path for isolated database tests
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_bot.db")
        await init_db(self.db_path)

    async def asyncTearDown(self):
        self.temp_dir.cleanup()

    async def test_database_logging_pipeline(self):
        user_id = 99999
        username = "integration_tester"
        first_name = "Tester"
        query = "Search python repositories"

        # 1. Upsert user
        await upsert_user(user_id, username, first_name, db_path=self.db_path)
        
        # 2. Log search
        await log_search(user_id, query, status="SUCCESS", db_path=self.db_path)

    def test_safety_and_routing_integration(self):
        # 3. Safety check URL
        url = "https://github.com/torvalds/linux"
        safety_result = ContentSafetyFilter.is_safe_url(url)
        self.assertTrue(safety_result["is_safe"])

        # 4. Route item with oversized file size to force direct_link
        route_result = DeliveryRouter.route_item(
            source_type="web",
            url=url,
            file_size=25 * 1024 * 1024  # 25MB > 20MB limit
        )
        self.assertEqual(route_result["route"], "direct_link")
        self.assertIn("Format markdown link", route_result["action_details"])

    def test_safety_blocking_dangerous_file(self):
        # Test dangerous file block
        safety_result = ContentSafetyFilter.is_safe_file("malware.exe")
        self.assertFalse(safety_result["is_safe"])
        self.assertIn("dangerous", safety_result["reason"].lower())

        # Route oversized or direct link
        route_result = DeliveryRouter.route_item(
            source_type="web",
            url="https://example.com/malware.exe",
            file_size=30 * 1024 * 1024
        )
        self.assertEqual(route_result["route"], "direct_link")


if __name__ == "__main__":
    unittest.main()
