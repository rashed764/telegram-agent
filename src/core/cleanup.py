import asyncio
import logging
from typing import Optional

from src.core.storage import StorageManager

logger = logging.getLogger(__name__)


class CleanupWorker:
    """
    Asynchronous background worker that periodically runs cleanup of old temporary files
    from the local staging storage manager.
    """

    def __init__(
        self,
        storage_manager: Optional[StorageManager] = None,
        interval_seconds: int = 300,  # 5 minutes default cleanup interval
        max_age_seconds: int = 3600    # 1 hour default max age
    ):
        self.storage_manager = storage_manager or StorageManager()
        self.interval_seconds = interval_seconds
        self.max_age_seconds = max_age_seconds
        self._task: Optional[asyncio.Task] = None
        self._is_running = False

    async def run_once(self) -> int:
        """
        Executes a single cleanup iteration, removing files older than max_age_seconds.
        
        Returns:
            Number of files removed.
        """
        try:
            removed_count = await asyncio.to_thread(
                self.storage_manager.cleanup_old_files,
                self.max_age_seconds
            )
            if removed_count > 0:
                logger.info(f"CleanupWorker removed {removed_count} expired temporary file(s).")
            return removed_count
        except Exception as e:
            logger.error(f"Error during CleanupWorker run_once: {e}")
            return 0

    async def start(self) -> None:
        """
        Starts the asynchronous background cleanup loop.
        Runs periodically until cancelled.
        """
        if self._is_running:
            logger.warning("CleanupWorker is already running.")
            return

        self._is_running = True
        logger.info(
            f"CleanupWorker started. Interval: {self.interval_seconds}s, Max File Age: {self.max_age_seconds}s."
        )

        try:
            while self._is_running:
                await self.run_once()
                await asyncio.sleep(self.interval_seconds)
        except asyncio.CancelledError:
            logger.info("CleanupWorker task cancelled gracefully.")
        except Exception as e:
            logger.error(f"CleanupWorker encountered unexpected error: {e}")
        finally:
            self._is_running = False
            logger.info("CleanupWorker stopped.")

    def stop(self) -> None:
        """Signals the background cleanup worker to stop."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()


async def start_cleanup_worker(
    interval_seconds: int = 300,
    max_age_seconds: int = 3600,
    storage_manager: Optional[StorageManager] = None
) -> CleanupWorker:
    """
    Factory function to initialize and start the background cleanup worker task.
    
    Returns:
        Running CleanupWorker instance.
    """
    worker = CleanupWorker(
        storage_manager=storage_manager,
        interval_seconds=interval_seconds,
        max_age_seconds=max_age_seconds
    )
    worker._task = asyncio.create_task(worker.start())
    # Yield control briefly to allow the task to begin execution
    await asyncio.sleep(0.01)
    return worker
