import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

MAX_TELEGRAM_BOT_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 MB in bytes


class DeliveryRouter:
    """
    Smart Delivery Routing Engine for deciding how to deliver or process scouted items
    based on file size, source type, and protocol limits.
    """

    @staticmethod
    def route_item(
        source_type: str,
        file_size: int = 0,
        url: Optional[str] = None,
        message_id: Optional[int] = None,
        entity: Optional[str] = None,
        file_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Determines the optimal delivery route for a scouted item.
        
        Routes:
        - 'direct_link': Direct Web Link → Format markdown link with warning alert.
        - 'stage_upload': File < 20MB & downloadable → Stage locally and prepare for upload.
        - 'telegram_forward': Telegram source → Prepare message/file forward.
        """
        source_type = source_type.lower()
        
        # 1. Telegram Source Routing
        if source_type in ["telegram", "telegram_scout"]:
            if file_size > MAX_TELEGRAM_BOT_UPLOAD_SIZE:
                return {
                    "route": "telegram_forward",
                    "action_details": f"Forward Telegram message ID {message_id} from {entity} (File size {file_size} bytes exceeds direct bot upload limit; forwarding via MTProto/Telegram native forward).",
                    "warning": "File size exceeds 20MB bot upload limit. Recommending native Telegram forward.",
                    "metadata": {
                        "source": source_type,
                        "entity": entity,
                        "message_id": message_id,
                        "file_size": file_size,
                        "file_name": file_name
                    }
                }
            return {
                "route": "telegram_forward",
                "action_details": f"Forward Telegram message ID {message_id} from entity {entity}.",
                "warning": None,
                "metadata": {
                    "source": source_type,
                    "entity": entity,
                    "message_id": message_id,
                    "file_size": file_size,
                    "file_name": file_name
                }
            }

        # 2. File Size < 20MB & Downloadable
        if file_size > 0 and file_size <= MAX_TELEGRAM_BOT_UPLOAD_SIZE:
            return {
                "route": "stage_upload",
                "action_details": f"Stage file '{file_name or 'unknown'}' locally (size: {file_size} bytes) and prepare for bot upload.",
                "warning": None,
                "metadata": {
                    "source": source_type,
                    "url": url,
                    "file_size": file_size,
                    "file_name": file_name
                }
            }

        # 3. Direct Web Link / Large File / Default Web source
        if url:
            if file_size > MAX_TELEGRAM_BOT_UPLOAD_SIZE:
                warning_msg = f"Warning: File size ({file_size / (1024*1024):.2f}MB) exceeds Telegram Bot 20MB limit. Provided as direct markdown link."
            else:
                warning_msg = "Notice: Direct web link provided. Access may require external browser download."

            return {
                "route": "direct_link",
                "action_details": f"Format markdown link for URL: {url}",
                "warning": warning_msg,
                "metadata": {
                    "source": source_type,
                    "url": url,
                    "file_size": file_size,
                    "file_name": file_name
                }
            }

        # Fallback default route
        return {
            "route": "direct_link",
            "action_details": "Default route: Direct link or informational response.",
            "warning": "No direct file or download link available.",
            "metadata": {
                "source": source_type,
                "file_size": file_size
            }
        }
