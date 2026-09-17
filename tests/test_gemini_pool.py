import asyncio
import os
import unittest
from unittest.mock import patch
from src.core.gemini_pool import GeminiKeyPool


class TestGeminiKeyPool(unittest.TestCase):

    @patch.dict(os.environ, {
        "GEMINI_API_KEY_1": "key_one",
        "GEMINI_API_KEY_2": "key_two",
        "GEMINI_API_KEY_3": "key_three",
    }, clear=True)
    def test_pool_initialization_and_rotation(self):
        pool = GeminiKeyPool()
        self.assertEqual(len(pool.keys), 3)
        
        k1 = pool.get_next_key()
        k2 = pool.get_next_key()
        self.assertNotEqual(k1, k2)

    def test_execute_with_rotation_success_on_retry(self):
        async def run():
            pool = GeminiKeyPool()
            pool.keys = ["key_fail", "key_success"]
            pool.key_status = {
                "key_fail": {"status": "active", "cooldown_until": 0.0},
                "key_success": {"status": "active", "cooldown_until": 0.0}
            }
            pool.current_index = 0

            call_count = 0

            async def mock_api_call(api_key, prompt):
                nonlocal call_count
                call_count += 1
                if api_key == "key_fail":
                    err = Exception("ResourceExhausted: 429 rate limit exceeded")
                    err.status_code = 429
                    raise err
                return f"Success with {api_key}"

            result = await pool.execute_with_rotation(mock_api_call, prompt="Hello Gemini")
            self.assertEqual(result, "Success with key_success")
            self.assertEqual(call_count, 2)
            self.assertEqual(pool.key_status["key_fail"]["status"], "exhausted")

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
