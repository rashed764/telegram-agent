import os
import logging
import httpx
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class MCPBridge:
    """
    Model Context Protocol (MCP) Bridge providing unified asynchronous access
    to Serper search, GitHub search, and Figma design inspection tools.
    """

    @staticmethod
    async def mcp_serper_search(query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """MCP wrapper for Serper.dev web search."""
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key or api_key == "your_serper_api_key_here":
            logger.warning("SERPER_API_KEY not configured for MCP bridge. Returning mock results.")
            return [{
                "title": f"MCP Mock Result for {query}",
                "url": "https://example.com/mcp-mock",
                "snippet": f"MCP Serper mock snippet for query: {query}"
            }]

        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        payload = {"q": query}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                results = []
                for item in data.get("organic", [])[:limit]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", "")
                    })
                return results
        except Exception as e:
            logger.error(f"MCP Serper search failed: {e}")
            return []

    @staticmethod
    async def mcp_github_search(query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """MCP wrapper for GitHub repository search."""
        token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN")
        url = "https://api.github.com/search/repositories"
        headers = {"Accept": "vnd.github.v3+json"}
        if token and not token.startswith("your_"):
            headers["Authorization"] = f"token {token}"

        params = {"q": query, "per_page": limit}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                results = []
                for item in data.get("items", []):
                    results.append({
                        "name": item.get("full_name", ""),
                        "url": item.get("html_url", ""),
                        "snippet": item.get("description", "") or "No description",
                        "size": item.get("size", 0)
                    })
                return results
        except Exception as e:
            logger.error(f"MCP GitHub search failed: {e}")
            return []

    @staticmethod
    async def mcp_figma_inspect(file_key: str) -> Dict[str, Any]:
        """MCP wrapper for Figma design file inspection."""
        token = os.getenv("FIGMA_ACCESS_TOKEN") or os.getenv("FIGMA_API_TOKEN")
        if not token or token.startswith("your_"):
            return {
                "file_key": file_key,
                "name": "Mock Figma Design File",
                "last_modified": "2026-09-16T00:00:00Z",
                "thumbnail_url": "https://example.com/figma-mock.png",
                "url": f"https://www.figma.com/file/{file_key}"
            }

        url = f"https://api.figma.com/v1/files/{file_key}"
        headers = {"X-Figma-Token": token}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                return {
                    "file_key": file_key,
                    "name": data.get("name", "Figma File"),
                    "last_modified": data.get("lastModified", ""),
                    "thumbnail_url": data.get("thumbnailUrl", ""),
                    "url": f"https://www.figma.com/file/{file_key}"
                }
        except Exception as e:
            logger.error(f"MCP Figma inspection failed: {e}")
            return {"error": str(e), "file_key": file_key}


def inspect_figma_file(file_key: str) -> Dict[str, Any]:
    """Synchronous helper for inspect_figma tool."""
    token = os.getenv("FIGMA_ACCESS_TOKEN") or os.getenv("FIGMA_API_TOKEN")
    if not token or token.startswith("your_"):
        return {
            "file_key": file_key,
            "name": "Mock Figma Design File",
            "last_modified": "2026-09-16T00:00:00Z",
            "thumbnail_url": "https://example.com/figma-mock.png",
            "url": f"https://www.figma.com/file/{file_key}"
        }

    url = f"https://api.figma.com/v1/files/{file_key}"
    headers = {"X-Figma-Token": token}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "file_key": file_key,
            "name": data.get("name", "Figma File"),
            "last_modified": data.get("lastModified", ""),
            "thumbnail_url": data.get("thumbnailUrl", ""),
            "url": f"https://www.figma.com/file/{file_key}"
        }
    except Exception as e:
        logger.error(f"Figma inspection failed: {e}")
        return {"error": str(e), "file_key": file_key}
