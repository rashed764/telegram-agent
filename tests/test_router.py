import unittest
from src.core.router import DeliveryRouter, MAX_TELEGRAM_BOT_UPLOAD_SIZE


class TestDeliveryRouter(unittest.TestCase):

    def test_route_direct_web_link(self):
        result = DeliveryRouter.route_item(
            source_type="web",
            url="https://example.com/document.pdf",
            file_size=0
        )
        self.assertEqual(result["route"], "direct_link")
        self.assertIn("Format markdown link", result["action_details"])
        self.assertIsNotNone(result["warning"])
        self.assertEqual(result["metadata"]["url"], "https://example.com/document.pdf")

    def test_route_stage_upload_small_file(self):
        small_size = 5 * 1024 * 1024  # 5 MB
        result = DeliveryRouter.route_item(
            source_type="web",
            url="https://example.com/small.zip",
            file_size=small_size,
            file_name="small.zip"
        )
        self.assertEqual(result["route"], "stage_upload")
        self.assertIn("Stage file 'small.zip' locally", result["action_details"])
        self.assertIsNone(result["warning"])
        self.assertEqual(result["metadata"]["file_size"], small_size)

    def test_route_telegram_source(self):
        result = DeliveryRouter.route_item(
            source_type="telegram",
            message_id=456,
            entity="@scout_channel",
            file_size=2 * 1024 * 1024  # 2MB
        )
        self.assertEqual(result["route"], "telegram_forward")
        self.assertIn("Forward Telegram message ID 456", result["action_details"])
        self.assertEqual(result["metadata"]["message_id"], 456)
        self.assertEqual(result["metadata"]["entity"], "@scout_channel")

    def test_route_telegram_source_oversized(self):
        large_size = 25 * 1024 * 1024  # 25 MB
        result = DeliveryRouter.route_item(
            source_type="telegram",
            message_id=789,
            entity="@large_files",
            file_size=large_size
        )
        self.assertEqual(result["route"], "telegram_forward")
        self.assertIsNotNone(result["warning"])
        self.assertIn("exceeds", result["warning"].lower())

    def test_route_web_oversized_file(self):
        large_size = 30 * 1024 * 1024  # 30 MB
        result = DeliveryRouter.route_item(
            source_type="web",
            url="https://example.com/huge.iso",
            file_size=large_size
        )
        self.assertEqual(result["route"], "direct_link")
        self.assertIsNotNone(result["warning"])
        self.assertIn("exceeds", result["warning"].lower())


if __name__ == "__main__":
    unittest.main()
