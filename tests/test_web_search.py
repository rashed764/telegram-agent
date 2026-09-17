import unittest
from unittest.mock import patch, MagicMock
from src.tools.web_search import search_web, scrape_url


class TestWebSearchTool(unittest.TestCase):

    @patch("src.tools.web_search.requests.get")
    def test_search_serpapi_success(self, mock_get):
        # Mock SerpAPI response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "organic_results": [
                {
                    "title": "Python Programming",
                    "link": "https://www.python.org",
                    "value": "...",
                    "snippet": "Python is a programming language..."
                }
            ]
        }
        mock_get.return_value = mock_response

        with patch.dict("os.environ", {"SERPAPI_API_KEY": "test_serpapi_key"}):
            results = search_web("Python", num_results=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Python Programming")
        self.assertEqual(results[0]["url"], "https://www.python.org")
        self.assertEqual(results[0]["snippet"], "Python is a programming language...")

    @patch("src.tools.web_search.requests.post")
    def test_search_duckduckgo_fallback(self, mock_post):
        # Mock DuckDuckGo HTML response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
          <body>
            <div class="result">
              <a class="result__url" href="https://example.com">Example Title</a>
              <a class="result__snippet">Example snippet text about testing.</a>
            </div>
          </body>
        </html>
        """
        mock_post.return_value = mock_response

        with patch.dict("os.environ", {"SERPAPI_API_KEY": "your_serpapi_key_here"}):
            results = search_web("example", num_results=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Example Title")
        self.assertEqual(results[0]["url"], "https://example.com")
        self.assertEqual(results[0]["snippet"], "Example snippet text about testing.")

    @patch("src.tools.web_search.requests.get")
    def test_scrape_url_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
          <head><title>Test Page Title</title></head>
          <body>
            <h1>Welcome</h1>
            <p>This is scraped page content.</p>
            <a href="https://example.com/page2">Link 2</a>
          </body>
        </html>
        """
        mock_get.return_value = mock_response

        result = scrape_url("https://example.com")
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["title"], "Test Page Title")
        self.assertIn("Welcome", result["text"])
        self.assertIn("This is scraped page content", result["text"])
        self.assertIn("https://example.com/page2", result["links"])


if __name__ == "__main__":
    unittest.main()
