import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Ensure the root directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.agent_brain import AgentBrain
from src.tools.github_search import search_github_repositories

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_invalid_model():
    print("=== Testing Invalid Model: gemini-3.5-flash-lite ===")
    brain = AgentBrain(model_name="gemini-3.5-flash-lite")
    try:
        res = await brain.think("Hi")
        print(f"SUCCESS (unexpected)! Response: {res}")
        return True
    except Exception as e:
        print(f"FAILED (expected) with exception: {e}")
        return False

async def test_valid_model_and_tool_flow():
    print("\n=== Testing Valid Model and Tool Execution Flow ===")
    # Using gemini-3.5-flash-lite since it actually worked with 200 OK!
    brain = AgentBrain(model_name="gemini-3.5-flash-lite")
    query = "Search GitHub for python templates"
    
    print(f"Sending Query: '{query}'")
    try:
        result = await brain.think(query)
        print("\n--- RAW LLM RESPONSE PARSED RESULTS ---")
        print(f"Thought: {result.get('thought')}")
        print(f"Plan: {result.get('plan')}")
        print(f"Tool Call: {result.get('tool_call')}")
        print(f"Response: {result.get('response')}")
        
        tool_call = result.get("tool_call")
        if tool_call:
            tool_name = tool_call.get("name")
            args = tool_call.get("arguments", {}) or {}
            print(f"\nVerification: Tool to dispatch is '{tool_name}' with args: {args}")
            
            if tool_name in ["search_github", "github_search"]:
                q = args.get("query") or args.get("q") or query
                print(f"Executing search_github_repositories with query: '{q}'")
                scout_results = search_github_repositories(q)
                print(f"Scout Results Found: {len(scout_results)}")
                if scout_results:
                    for i, r in enumerate(scout_results[:3]):
                        print(f"[{i+1}] Name: {r['full_name']}, Stars: {r['stargazers_count']}, Link: {r['html_url']}")
                else:
                    print("No results returned from GitHub API.")
        else:
            print("No tool call was made by the agent.")
            
    except Exception as e:
        print(f"Thinking flow failed: {e}")

async def main():
    load_dotenv()
    # Test invalid model first
    await test_invalid_model()
    # Test valid model and tool dispatch
    await test_valid_model_and_tool_flow()

if __name__ == "__main__":
    asyncio.run(main())
