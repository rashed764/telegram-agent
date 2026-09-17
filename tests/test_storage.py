import unittest
from unittest.mock import patch, MagicMock
import tempfile
from pathlib import Path
import time
import os
import requests

from src.core.storage import (
    StorageManager,
    StorageError,
    OversizedFileError,
    DownloadError
)


class TestStorageManager(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for isolated storage tests
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_manager = StorageManager(storage_dir=self.temp_dir.name, max_size=1024 * 1024)  # 1MB max for testing

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_ensure_storage_dir(self):
        path = self.storage_manager.ensure_storage_dir()
        self.assertTrue(path.exists())
        self.assertTrue(path.is_dir())

    @patch("src.core.storage.requests.get")
    def test_download_file_success(self, mock_get):
        # Mock requests.get response
        mock_response = MagicMock()
        mock_response.headers = {"Content-Length": "100"}
        mock_response.iter_content.return_value = [b"a" * 50, b"b" * 50]
        mock_get.return_value = mock_response

        result = self.storage_manager.download_file(
            url="https://example.com/testfile.txt",
            filename="testfile.txt"
        )

        self.assertEqual(result["file_name"], "testfile.txt")
        self.assertEqual(result["file_size"], 100)
        self.assertTrue(Path(result["file_path"]).exists())
        
        # Verify content written correctly
        with open(result["file_path"], "rb") as f:
            content = f.read()
        self.assertEqual(content, b"a" * 50 + b"b" * 50)

    @patch("src.core.storage.requests.get")
    def test_download_file_oversized_content_length(self, mock_get):
        # Mock response with Content-Length exceeding 1MB limit
        mock_response = MagicMock()
        mock_response.headers = {"Content-Length": str(2 * 1024 * 1024)}  # 2MB
        mock_get.return_value = mock_response

        with self.assertRaises(OversizedFileError):
            self.storage_manager.download_file(
                url="https://example.com/largefile.iso"
            )
        mock_response.close.assert_called_once()

    @patch("src.core.storage.requests.get")
    def test_download_file_oversized_stream(self, mock_get):
        # Mock response without Content-Length header, but stream exceeds limit
        mock_response = MagicMock()
        mock_response.headers = {}
        # Chunks totaling 1.5MB (exceeds 1MB limit)
        mock_response.iter_content.return_value = [b"a" * (512 * 1024), b"b" * (1024 * 1024)]
        mock_get.return_value = mock_response

        with self.assertRaises(OversizedFileError):
            self.storage_manager.download_file(
                url="https://example.com/streamlarge.bin",
                filename="streamlarge.bin"
            )

    @patch("src.core.storage.requests.get")
    def test_download_file_network_error(self, mock_get):
        mock_get.side_effect = requests.RequestException("Connection refused")

        with self.assertRaises(DownloadError):
            self.storage_manager.download_file(
                url="https://example.com/unreachable.txt"
            )

    def test_storage_stats_and_clear(self):
        # Initially empty
        stats = self.storage_manager.get_storage_stats()
        self.assertEqual(stats["file_count"], 0)
        self.assertEqual(stats["total_size_bytes"], 0)

        # Create dummy files
        file1 = Path(self.storage_manager.storage_dir) / "file1.txt"
        file2 = Path(self.storage_manager.storage_dir) / "file2.txt"
        file1.write_bytes(b"hello")
        file2.write_bytes(b"world!")

        stats_after = self.storage_manager.get_storage_stats()
        self.assertEqual(stats_after["file_count"], 2)
        self.assertEqual(stats_after["total_size_bytes"], 11)

        # Clear storage
        deleted = self.storage_manager.clear_storage()
        self.assertEqual(deleted, 2)

        stats_cleared = self.storage_manager.get_storage_stats()
        self.assertEqual(stats_cleared["file_count"], 0)

    def test_cleanup_old_files(self):
        storage_dir = Path(self.storage_manager.storage_dir)
        old_file = storage_dir / "old.txt"
        new_file = storage_dir / "new.txt"

        old_file.write_bytes(b"old content")
        new_file.write_bytes(b"new content")

        # Backdate old_file mtime by 2 days (172800 seconds)
        old_mtime = time.time() - 172800
        os.utime(old_file, (old_mtime, old_mtime))

        # Cleanup files older than 1 day (86400 seconds)
        removed = self.storage_manager.cleanup_old_files(max_age_seconds=86400)
        self.assertEqual(removed, 1)
        self.assertFalse(old_file.exists())
        self.assertTrue(new_file.exists())


if __name__ == "__main__":
    unittest.main()
