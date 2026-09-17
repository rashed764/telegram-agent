import unittest
from unittest.mock import patch, MagicMock
from src.tools.github_search import search_github_repositories, search_github_code, get_github_releases


class TestGitHubSearchTool(unittest.TestCase):

    @patch("src.tools.github_search.requests.get")
    def test_search_github_repositories_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "name": "telegram-agent",
                    "full_name": "user/telegram-agent",
                    "description": "An autonomous AI agent for Telegram",
                    "html_url": "https://github.com/user/telegram-agent",
                    "stargazers_count": 42,
                    "language": "Python",
                    "updated_at": "2026-09-16T00:00:00Z"
                }
            ]
        }
        mock_get.return_value = mock_response

        results = search_github_repositories("telegram agent")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "telegram-agent")
        self.assertEqual(results[0]["stargazers_count"], 42)
        self.assertEqual(results[0]["language"], "Python")
        self.assertEqual(results[0]["html_url"], "https://github.com/user/telegram-agent")

    @patch("src.tools.github_search.requests.get")
    def test_search_github_code_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "name": "agent_brain.py",
                    "path": "src/core/agent_brain.py",
                    "html_url": "https://github.com/user/repo/blob/main/src/core/agent_brain.py",
                    "repository": {
                        "name": "repo",
                        "full_name": "user/repo",
                        "owner": {"login": "user"}
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        results = search_github_code("AgentBrain")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "agent_brain.py")
        self.assertEqual(results[0]["path"], "src/core/agent_brain.py")
        self.assertIn("raw.githubusercontent.com", results[0]["raw_url"])

    @patch("src.tools.github_search.requests.get")
    def test_get_github_releases_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "tag_name": "v1.0.0",
                "name": "Initial Release",
                "html_url": "https://github.com/user/repo/releases/tag/v1.0.0",
                "published_at": "2026-09-16T00:00:00Z",
                "assets": [
                    {
                        "name": "app.zip",
                        "browser_download_url": "https://github.com/user/repo/releases/download/v1.0.0/app.zip",
                        "size": 1024
                    }
                ]
            }
        ]
        mock_get.return_value = mock_response

        results = get_github_releases("user", "repo")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["tag_name"], "v1.0.0")
        self.assertEqual(len(results[0]["assets"]), 1)
        self.assertEqual(results[0]["assets"][0]["name"], "app.zip")


if __name__ == "__main__":
    unittest.main()
