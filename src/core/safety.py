import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Blacklist of dangerous or executable file extensions
DANGEROUS_EXTENSIONS = {
    ".exe", ".scr", ".bat", ".vbs", ".msi", ".pif",
    ".cmd", ".com", ".reg", ".js", ".jse", ".wsf",
    ".wsh", ".ps1", ".hta", ".cpl", ".msc", ".jar"
}

# Dangerous MIME types
DANGEROUS_MIME_TYPES = {
    "application/x-msdownload",
    "application/x-executable",
    "application/x-msdos-program",
    "application/vnd.microsoft.portable-executable",
    "application/x-bat",
    "application/javascript"
}

# Allowed URL schemes
ALLOWED_URL_SCHEMES = {"http", "https"}


class ContentSafetyFilter:
    """
    Content safety and moderation filter for screening files, extensions, MIME types,
    and URLs before downloading, staging, or processing.
    """

    @staticmethod
    def is_safe_file(filename: str, mime_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Screens a file by its extension and optional MIME type against known executable/dangerous lists.
        
        Args:
            filename: Name or path of the file.
            mime_type: Optional MIME type of the file.
            
        Returns:
            Dict containing 'is_safe' (bool), 'reason' (str or None), and 'details'.
        """
        if not filename:
            return {
                "is_safe": False,
                "reason": "Filename is missing or empty.",
                "details": {"filename": filename, "mime_type": mime_type}
            }

        ext = Path(filename).suffix.lower()
        
        # Check extension blacklist
        if ext in DANGEROUS_EXTENSIONS:
            reason = f"Blocked dangerous file extension '{ext}'."
            logger.warning(f"Safety violation: {reason} (File: {filename})")
            return {
                "is_safe": False,
                "reason": reason,
                "details": {"extension": ext, "filename": filename, "mime_type": mime_type}
            }

        # Check MIME type blacklist if provided
        if mime_type:
            mime_lower = mime_type.lower().strip()
            if mime_lower in DANGEROUS_MIME_TYPES:
                reason = f"Blocked dangerous MIME type '{mime_type}'."
                logger.warning(f"Safety violation: {reason} (File: {filename})")
                return {
                    "is_safe": False,
                    "reason": reason,
                    "details": {"extension": ext, "filename": filename, "mime_type": mime_type}
                }

        return {
            "is_safe": True,
            "reason": None,
            "details": {"extension": ext, "filename": filename, "mime_type": mime_type}
        }

    @staticmethod
    def is_safe_url(url: str) -> Dict[str, Any]:
        """
        Screens a URL for structural safety, valid schemes, and safe access parameters.
        
        Args:
            url: The URL string to screen.
            
        Returns:
            Dict containing 'is_safe' (bool), 'reason' (str or None), and 'details'.
        """
        if not url or not isinstance(url, str):
            return {
                "is_safe": False,
                "reason": "URL is missing, empty, or invalid type.",
                "details": {"url": url}
            }

        url = url.strip()
        try:
            parsed = urlparse(url)
        except Exception as e:
            return {
                "is_safe": False,
                "reason": f"Failed to parse URL: {e}",
                "details": {"url": url}
            }

        # Validate scheme
        if parsed.scheme.lower() not in ALLOWED_URL_SCHEMES:
            reason = f"Blocked URL scheme '{parsed.scheme}': only http and https are permitted."
            logger.warning(f"Safety violation: {reason} (URL: {url})")
            return {
                "is_safe": False,
                "reason": reason,
                "details": {"scheme": parsed.scheme, "netloc": parsed.netloc}
            }

        # Validate netloc (domain/host) presence
        if not parsed.netloc:
            reason = "Malformed URL: missing domain or host."
            return {
                "is_safe": False,
                "reason": reason,
                "details": {"url": url}
            }

        return {
            "is_safe": True,
            "reason": None,
            "details": {"scheme": parsed.scheme, "netloc": parsed.netloc, "path": parsed.path}
        }
