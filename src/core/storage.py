import os
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests

logger = logging.getLogger(__name__)

DEFAULT_STORAGE_DIR = "data/downloads"
MAX_DOWNLOAD_SIZE = 20 * 1024 * 1024  # 20 MB


class StorageError(Exception):
    """Base exception for storage and download operations."""
    pass


class OversizedFileError(StorageError):
    """Raised when a file exceeds the maximum allowed download size."""
    pass


class DownloadError(StorageError):
    """Raised when a file download fails due to network or HTTP errors."""
    pass


class StorageManager:
    """
    Manages local caching and temporary staging directory (default: data/downloads/)
    with file downloading utilities, size enforcement, and storage tracking.
    """

    def __init__(self, storage_dir: str = DEFAULT_STORAGE_DIR, max_size: int = MAX_DOWNLOAD_SIZE):
        self.storage_dir = Path(storage_dir)
        self.max_size = max_size
        self.ensure_storage_dir()

    def ensure_storage_dir(self) -> Path:
        """Ensures that the staging storage directory exists."""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create storage directory {self.storage_dir}: {e}")
            raise StorageError(f"Could not create storage directory: {e}")
        return self.storage_dir

    def download_file(
        self,
        url: str,
        filename: Optional[str] = None,
        custom_max_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Downloads a file from a URL with size checks, streaming chunks, and exception handling.
        
        Args:
            url: The download URL.
            filename: Optional custom filename. If not provided, derived from URL.
            custom_max_size: Optional override for max allowed file size in bytes.
            
        Returns:
            Dict containing file metadata ('file_path', 'file_name', 'file_size', 'url').
            
        Raises:
            OversizedFileError: If file size exceeds max_size limit.
            DownloadError: If network request or writing fails.
        """
        max_allowed_size = custom_max_size if custom_max_size is not None else self.max_size
        self.ensure_storage_dir()

        # Derive filename if not provided
        if not filename:
            path_part = url.split("?")[0]
            filename = os.path.basename(path_part)
            if not filename or "." not in filename:
                filename = f"download_{int(time.time())}.bin"

        # Sanitize filename
        filename = "".join(c for c in filename if c.isalnum() or c in "._- ").strip()
        if not filename:
            filename = f"download_{int(time.time())}.bin"

        target_path = self.storage_dir / filename

        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Network error downloading {url}: {e}")
            raise DownloadError(f"Failed to connect or download from {url}: {e}")

        # Check Content-Length header if available
        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                total_size = int(content_length)
                if total_size > max_allowed_size:
                    response.close()
                    raise OversizedFileError(
                        f"File size ({total_size} bytes) exceeds maximum allowed size of {max_allowed_size} bytes."
                    )
            except ValueError:
                pass

        downloaded_size = 0
        chunk_size = 8192

        try:
            with open(target_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        downloaded_size += len(chunk)
                        if downloaded_size > max_allowed_size:
                            f.close()
                            if target_path.exists():
                                target_path.unlink()
                            raise OversizedFileError(
                                f"Downloaded size exceeded maximum allowed limit of {max_allowed_size} bytes."
                            )
                        f.write(chunk)
        except OversizedFileError:
            raise
        except Exception as e:
            if target_path.exists():
                try:
                    target_path.unlink()
                except Exception:
                    pass
            logger.error(f"Error writing downloaded file {filename}: {e}")
            raise DownloadError(f"Failed to save downloaded file {filename}: {e}")

        file_stats = target_path.stat()
        logger.info(f"Successfully downloaded and staged {filename} ({file_stats.st_size} bytes) at {target_path}")

        return {
            "file_path": str(target_path.resolve()),
            "file_name": filename,
            "file_size": file_stats.st_size,
            "url": url
        }

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Returns statistics about the local staging directory.
        
        Returns:
            Dict containing 'file_count', 'total_size_bytes', 'storage_dir'.
        """
        self.ensure_storage_dir()
        file_count = 0
        total_size = 0

        try:
            for item in self.storage_dir.iterdir():
                if item.is_file():
                    file_count += 1
                    total_size += item.stat().st_size
        except Exception as e:
            logger.error(f"Error computing storage stats for {self.storage_dir}: {e}")

        return {
            "file_count": file_count,
            "total_size_bytes": total_size,
            "storage_dir": str(self.storage_dir.resolve())
        }

    def clear_storage(self) -> int:
        """
        Deletes all files in the storage directory.
        
        Returns:
            Number of files deleted.
        """
        self.ensure_storage_dir()
        deleted_count = 0

        try:
            for item in self.storage_dir.iterdir():
                if item.is_file():
                    item.unlink()
                    deleted_count += 1
            logger.info(f"Cleared storage directory {self.storage_dir}. Deleted {deleted_count} files.")
        except Exception as e:
            logger.error(f"Error clearing storage directory {self.storage_dir}: {e}")

        return deleted_count

    def cleanup_old_files(self, max_age_seconds: int = 86400) -> int:
        """
        Removes files older than max_age_seconds from the storage directory.
        
        Args:
            max_age_seconds: Maximum age of files in seconds (default: 24 hours).
            
        Returns:
            Number of old files removed.
        """
        self.ensure_storage_dir()
        current_time = time.time()
        removed_count = 0

        try:
            for item in self.storage_dir.iterdir():
                if item.is_file():
                    file_age = current_time - item.stat().st_mtime
                    if file_age > max_age_seconds:
                        item.unlink()
                        removed_count += 1
            logger.info(f"Cleaned up {removed_count} files older than {max_age_seconds} seconds.")
        except Exception as e:
            logger.error(f"Error during old files cleanup in {self.storage_dir}: {e}")

        return removed_count
