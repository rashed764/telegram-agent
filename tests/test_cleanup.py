import unittest
import asyncio
import tempfile
from pathlib import Path
import time
import os

from src.core.storage import StorageManager
from src.core.cleanup import CleanupWorker, start_cleanup_worker


class TestCleanupWorker(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_manager = StorageManager(storage_dir=self.temp_dir.name, max_size=1024 * 1024)

    async def asyncTearDown(self):
        self.temp_dir.cleanup()

    async def test_cleanup_worker_run_once(self):
        storage_path = Path(self.storage_manager.storage_dir)
        old_file = storage_path / "expired.tmp"
        new_file = storage_path / "active.tmp"

        old_file.write_bytes(b"old data")
        new_file.write_bytes(b"new data")

        old_mtime = time.time() - 7200
        os.utime(old_file, (old_mtime, old_mtime))

        worker = CleanupWorker(
            storage_manager=self.storage_manager,
            interval_seconds=60,
            max_age_seconds=3600
        )

        removed_count = await worker.run_once()
        self.assertEqual(removed_count, 1)
        self.assertFalse(old_file.exists())
        self.assertTrue(new_file.exists())

    async def test_cleanup_worker_lifecycle_and_cancellation(self):
        worker = CleanupWorker(
            storage_manager=self.storage_manager,
            interval_seconds=0.5,  # Longer interval so it stays in sleep during test
            max_age_seconds=3600
        )

        task = asyncio.create_task(worker.start())
        worker._task = task

        # Give it time to start and enter sleep
        await asyncio.sleep(0.1)

        self.assertTrue(worker._is_running)

        worker.stop()
        
        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.CancelledError:
            pass

        self.assertFalse(worker._is_running)
        self.assertTrue(task.done())

    async def test_start_cleanup_worker_factory(self):
        worker = await start_cleanup_worker(
            interval_seconds=0.5,
            max_age_seconds=3600,
            storage_manager=self.storage_manager
        )

        try:
            self.assertIsNotNone(worker._task)
            if worker._task.done() and worker._task.exception():
                raise worker._task.exception()
            self.assertTrue(worker._is_running)
        finally:
            worker.stop()
            if worker._task and not worker._task.done():
                try:
                    await asyncio.wait_for(worker._task, timeout=1.0)
                except asyncio.CancelledError:
                    pass


if __name__ == "__main__":
    unittest.main()
