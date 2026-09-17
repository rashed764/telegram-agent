import os
import re
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from google import genai
from google.genai import types
from src.core.gemini_pool import GeminiKeyPool

logger = logging.getLogger(__name__)

AGENT_SYSTEM_PROMPT = """You are an autonomous File Scout AI Agent for Telegram equipped with Model Context Protocol (MCP) tool execution support. You solve user requests by thinking step-by-step using Chain of Thought (CoT) reasoning before deciding whether to call a tool or respond directly.

You must structure your reasoning output using the following XML-like tags:
<thought>Analyze the user query, context, and available tools. Explain your reasoning.</thought>
<plan>Outline the precise step(s) to fulfill the request.</plan>
<tool_call>
{
  "name": "tool_name",
  "arguments": {
    "arg1": "val1"
  }
}
</tool_call>
<response>Final text response to the user (use if no tool call is needed or as a concluding remark).</response>

Available Tools & Parameters:
1. `search_web` (or `mcp_serper_search`)
   - Description: Search the web for information, documentation, or links.
   - Arguments: `{"query": "search query string"}`
2. `search_github` (or `mcp_github_search`)
   - Description: Search GitHub repositories or code for projects, templates, and files.
   - Arguments: `{"query": "search query string"}`
3. `search_telegram`
   - Description: Search messages or files within accessible Telegram channels or groups.
   - Arguments: `{"entity": "channel or group username", "query": "search query string"}`
4. `inspect_figma` (or `mcp_figma_inspect`)
   - Description: Inspect Figma design files and metadata.
   - Arguments: `{"file_key": "figma file key"}`

If the user query is a greeting, casual conversation, or doesn't require search/files, do NOT output a <tool_call>. Instead, respond directly via <response>. Always output valid JSON inside `<tool_call>` if you decide to invoke a tool.
"""


class AgentBrain:
    def __init__(self, model_name: Optional[str] = None, gemini_pool: Optional[GeminiKeyPool] = None):
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        self.gemini_pool = gemini_pool or GeminiKeyPool()

    def parse_agent_output(self, raw_text: str) -> Dict[str, Any]:
        """
        Parses structured agent output containing CoT tags (<thought>, <plan>, <tool_call>, <response>).
        Extracts tool call JSON if present, even inside markdown code blocks.
        """
        result = {
            "thought": "",
            "plan": "",
            "tool_call": None,
            "response": "",
            "raw": raw_text
        }

        if not raw_text:
            return result

        # Extract <thought>
        thought_match = re.search(r"<thought>(.*?)</thought>", raw_text, re.DOTALL | re.IGNORECASE)
        if thought_match:
            result["thought"] = thought_match.group(1).strip()

        # Extract <plan>
        plan_match = re.search(r"<plan>(.*?)</plan>", raw_text, re.DOTALL | re.IGNORECASE)
        if plan_match:
            result["plan"] = plan_match.group(1).strip()

        # Extract <response>
        response_match = re.search(r"<response>(.*?)</response>", raw_text, re.DOTALL | re.IGNORECASE)
        if response_match:
            result["response"] = response_match.group(1).strip()

        # Extract <tool_call>
        tool_call_match = re.search(r"<tool_call>(.*?)</tool_call>", raw_text, re.DOTALL | re.IGNORECASE)
        if not tool_call_match:
            tool_call_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)

        if tool_call_match:
            tool_content = tool_call_match.group(1).strip()
            cleaned_json = re.sub(r"^```(?:json)?\s*", "", tool_content)
            cleaned_json = re.sub(r"\s*```$", "", cleaned_json)
            cleaned_json = cleaned_json.strip()

            try:
                parsed_json = json.loads(cleaned_json)
                if isinstance(parsed_json, dict) and "name" in parsed_json:
                    if "arguments" not in parsed_json:
                        args = {k: v for k, v in parsed_json.items() if k != "name"}
                        parsed_json["arguments"] = args
                    result["tool_call"] = parsed_json
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse tool_call JSON: {e}. Content: {cleaned_json}")
                result["tool_call"] = {"raw_content": cleaned_json, "error": str(e)}

        return result

    async def think(self, user_query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Sends user query and context to Gemini Lite model via gemini_pool with rotation,
        enforcing CoT system prompt, and returns parsed structured output.
        """
        context_str = f"\nContext/State: {json.dumps(context)}" if context else ""
        prompt = f"{user_query}{context_str}"

        async def _api_call(api_key: str) -> str:
            client = genai.Client(api_key=api_key)
            config = types.GenerateContentConfig(
                system_instruction=AGENT_SYSTEM_PROMPT,
                temperature=0.2,
                max_output_tokens=1024,
            )
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            return response.text

        try:
            raw_output = await self.gemini_pool.execute_with_rotation(_api_call)
            logger.info(f"--- RAW LLM RESPONSE ---\n{raw_output}\n------------------------")
            return self.parse_agent_output(raw_output)
        except Exception as e:
            logger.exception(f"AgentBrain thinking failed: {e}")
            raise
