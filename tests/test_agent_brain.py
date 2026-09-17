import asyncio
import unittest
from unittest.mock import patch, MagicMock
from src.core.agent_brain import AgentBrain
from src.core.gemini_pool import GeminiKeyPool


class TestAgentBrain(unittest.TestCase):

    def setUp(self):
        self.brain = AgentBrain(model_name="gemini-2.0-flash")

    def test_parse_agent_output_full(self):
        raw_output = """
        <thought>
        The user wants to search for PDF files in their directory. I should use the file_search tool.
        </thought>
        <plan>
        1. Call file_search with query '*.pdf'.
        2. Present results to user.
        </plan>
        <tool_call>
        ```json
        {
          "name": "file_search",
          "arguments": {
            "pattern": "*.pdf"
          }
        }
        ```
        </tool_call>
        """
        parsed = self.brain.parse_agent_output(raw_output)
        self.assertIn("user wants to search", parsed["thought"])
        self.assertIn("1. Call file_search", parsed["plan"])
        self.assertIsNotNone(parsed["tool_call"])
        self.assertEqual(parsed["tool_call"]["name"], "file_search")
        self.assertEqual(parsed["tool_call"]["arguments"]["pattern"], "*.pdf")
        self.assertEqual(parsed["response"], "")

    def test_parse_agent_output_response_only(self):
        raw_output = """
        <thought>
        The user is saying hello. No tool is needed.
        </thought>
        <plan>
        Respond cordially.
        </plan>
        <response>
        Hello! How can I help you scout files today?
        </response>
        """
        parsed = self.brain.parse_agent_output(raw_output)
        self.assertIn("user is saying hello", parsed["thought"])
        self.assertEqual(parsed["tool_call"], None)
        self.assertEqual(parsed["response"], "Hello! How can I help you scout files today?")

    def test_parse_agent_output_invalid_json_tool_call(self):
        raw_output = """
        <thought>Testing invalid JSON handling</thought>
        <plan>Call broken tool</plan>
        <tool_call>
        { name: broken_json }
        </tool_call>
        """
        parsed = self.brain.parse_agent_output(raw_output)
        self.assertIsNotNone(parsed["tool_call"])
        self.assertIn("error", parsed["tool_call"])

    def test_think_with_mocked_gemini(self):
        async def run():
            mock_pool = MagicMock(spec=GeminiKeyPool)
            
            async def mock_execute(func, *args, **kwargs):
                # Simulate return of generate_content text
                return """
                <thought>Mocked thought process</thought>
                <plan>Mocked plan</plan>
                <response>Hello from mock Gemini!</response>
                """

            mock_pool.execute_with_rotation = mock_execute

            brain = AgentBrain(model_name="gemini-2.0-flash", gemini_pool=mock_pool)
            result = await brain.think("Hi there")

            self.assertEqual(result["thought"], "Mocked thought process")
            self.assertEqual(result["plan"], "Mocked plan")
            self.assertEqual(result["response"], "Hello from mock Gemini!")
            self.assertIsNone(result["tool_call"])

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
