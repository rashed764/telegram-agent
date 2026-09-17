import unittest

from src.core.safety import ContentSafetyFilter, DANGEROUS_EXTENSIONS


class TestContentSafetyFilter(unittest.TestCase):

    def test_safe_file_extensions(self):
        safe_files = [
            "document.pdf",
            "archive.zip",
            "image.png",
            "data.csv",
            "script.py"  # Python code script is not in dangerous binary blacklist
        ]
        for filename in safe_files:
            result = ContentSafetyFilter.is_safe_file(filename)
            self.assertTrue(result["is_safe"], f"File '{filename}' should be considered safe.")
            self.assertIsNone(result["reason"])

    def test_dangerous_file_extensions(self):
        dangerous_files = [
            "setup.exe",
            "update.bat",
            "script.vbs",
            "installer.msi",
            "screensaver.scr",
            "payload.cmd",
            "malware.com",
            "hack.ps1"
        ]
        for filename in dangerous_files:
            result = ContentSafetyFilter.is_safe_file(filename)
            self.assertFalse(result["is_safe"], f"File '{filename}' should be blocked as dangerous.")
            self.assertIsNotNone(result["reason"])
            self.assertIn("extension", result["details"])

    def test_dangerous_mime_types(self):
        result = ContentSafetyFilter.is_safe_file(
            filename="unknown_file.bin",
            mime_type="application/x-msdownload"
        )
        self.assertFalse(result["is_safe"])
        self.assertIn("MIME type", result["reason"])

    def test_safe_urls(self):
        safe_urls = [
            "https://example.com/download/file.pdf",
            "http://github.com/repo/archive.zip",
            "https://api.github.com/repos/owner/repo"
        ]
        for url in safe_urls:
            result = ContentSafetyFilter.is_safe_url(url)
            self.assertTrue(result["is_safe"], f"URL '{url}' should be safe.")
            self.assertIsNone(result["reason"])

    def test_unsafe_urls(self):
        unsafe_urls = [
            "ftp://example.com/file.zip",
            "file:///C:/Windows/System32/cmd.exe",
            "javascript:alert('xss')",
            "not_a_url",
            ""
        ]
        for url in unsafe_urls:
            result = ContentSafetyFilter.is_safe_url(url)
            self.assertFalse(result["is_safe"], f"URL '{url}' should be blocked.")
            self.assertIsNotNone(result["reason"])


if __name__ == "__main__":
    unittest.main()
