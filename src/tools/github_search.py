import os
import logging
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def _get_headers() -> Dict[str, str]:
    token = os.getenv("GITHUB_API_TOKEN") or os.getenv("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    if token and not token.startswith("your_"):
        headers["Authorization"] = f"Bearer {token}"
    return headers


def search_github_repositories(query: str, sort: str = "stars", order: str = "desc", per_page: int = 5) -> List[Dict[str, Any]]:
    """
    Searches GitHub repositories using the GitHub REST API.
    Returns structured results including repository links, descriptions, stars, and language.
    """
    url = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": sort,
        "order": order,
        "per_page": per_page
    }
    try:
        response = requests.get(url, headers=_get_headers(), params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("items", []):
            results.append({
                "name": item.get("name", ""),
                "full_name": item.get("full_name", ""),
                "description": item.get("description", ""),
                "html_url": item.get("html_url", ""),
                "stargazers_count": item.get("stargazers_count", 0),
                "language": item.get("language", ""),
                "updated_at": item.get("updated_at", "")
            })
        return results
    except Exception as e:
        logger.error(f"GitHub repository search failed for query '{query}': {e}")
        return []


def search_github_code(query: str, per_page: int = 5) -> List[Dict[str, Any]]:
    """
    Searches GitHub code files using the GitHub REST API.
    Returns structured results including repository links, file paths, and raw file URLs.
    """
    url = "https://api.github.com/search/code"
    params = {
        "q": query,
        "per_page": per_page
    }
    try:
        response = requests.get(url, headers=_get_headers(), params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("items", []):
            repository = item.get("repository", {})
            owner = repository.get("owner", {}).get("login", "")
            repo_name = repository.get("name", "")
            path = item.get("path", "")
            html_url = item.get("html_url", "")
            
            # Construct raw file URL if possible
            # e.g., https://raw.githubusercontent.com/owner/repo/main/path
            raw_url = ""
            if owner and repo_name and path:
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/main/{path}"

            results.append({
                "name": item.get("name", ""),
                "path": path,
                "html_url": html_url,
                "raw_url": raw_url,
                "repository": repository.get("full_name", "")
            })
        return results
    except Exception as e:
        logger.error(f"GitHub code search failed for query '{query}': {e}")
        return []


def get_github_releases(owner: str, repo: str, per_page: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieves GitHub repository releases and their assets.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    params = {"per_page": per_page}
    try:
        response = requests.get(url, headers=_get_headers(), params=params, timeout=10)
        response.raise_for_status()
        releases = response.json()

        results = []
        for rel in releases[:per_page]:
            assets = []
            for asset in rel.get("assets", []):
                assets.append({
                    "name": asset.get("name", ""),
                    "download_url": asset.get("browser_download_url", ""),
                    "size": asset.get("size", 0)
                })

            results.append({
                "tag_name": rel.get("tag_name", ""),
                "name": rel.get("name", ""),
                "html_url": rel.get("html_url", ""),
                "published_at": rel.get("published_at", ""),
                "assets": assets
            })
        return results
    except Exception as e:
        logger.error(f"Failed to fetch releases for {owner}/{repo}: {e}")
        return []
