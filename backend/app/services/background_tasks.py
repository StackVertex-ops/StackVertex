"""Background Task System.

Simple threading-based background task execution for deployments.
Future: Migrate to Celery for production.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class BackgroundTaskRunner:
    """Manages background task execution using thread pool."""

    _instance: Optional['BackgroundTaskRunner'] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern for global task runner."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize thread pool executor."""
        if not hasattr(self, 'executor'):
            self.executor = ThreadPoolExecutor(
                max_workers=5,  # Max concurrent deployments
                thread_name_prefix="bg_task_"
            )
            self.tasks: dict[UUID, Future] = {}
            logger.info("BackgroundTaskRunner initialized with 5 workers")

    def submit_task(
        self,
        task_id: UUID,
        func: Callable,
        *args,
        **kwargs
    ) -> Future:
        """Submit task to background executor.

        Args:
            task_id: Unique task identifier (deployment ID)
            func: Function to execute in background
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Future object for task tracking
        """
        logger.info(f"Submitting background task {task_id}")

        future = self.executor.submit(self._wrap_task, task_id, func, *args, **kwargs)
        self.tasks[task_id] = future

        # Cleanup completed tasks
        self._cleanup_completed_tasks()

        return future

    def _wrap_task(
        self,
        task_id: UUID,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Wrap task execution with logging and error handling.

        Args:
            task_id: Task identifier
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result from func execution
        """
        logger.info(f"Task {task_id} started at {datetime.utcnow()}")
        start_time = datetime.utcnow()

        try:
            result = func(*args, **kwargs)
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Task {task_id} completed successfully in {elapsed:.2f}s")
            return result

        except Exception as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Task {task_id} failed after {elapsed:.2f}s: {e}", exc_info=True)
            raise

        finally:
            # Remove from tracking
            if task_id in self.tasks:
                del self.tasks[task_id]

    def get_task_status(self, task_id: UUID) -> str | None:
        """Get task status.

        Args:
            task_id: Task identifier

        Returns:
            Status string: "running", "completed", "failed", or None if not found
        """
        if task_id not in self.tasks:
            return None

        future = self.tasks[task_id]

        if future.running():
            return "running"
        elif future.done():
            if future.exception():
                return "failed"
            else:
                return "completed"
        else:
            return "pending"

    def cancel_task(self, task_id: UUID) -> bool:
        """Cancel running task.

        Args:
            task_id: Task identifier

        Returns:
            True if cancelled, False if not found or already completed
        """
        if task_id not in self.tasks:
            logger.warning(f"Task {task_id} not found for cancellation")
            return False

        future = self.tasks[task_id]

        if future.cancel():
            logger.info(f"Task {task_id} cancelled successfully")
            del self.tasks[task_id]
            return True
        else:
            logger.warning(f"Task {task_id} could not be cancelled (already running/completed)")
            return False

    def _cleanup_completed_tasks(self):
        """Remove completed tasks from tracking."""
        completed_tasks = [
            task_id for task_id, future in self.tasks.items()
            if future.done()
        ]

        for task_id in completed_tasks:
            del self.tasks[task_id]

        if completed_tasks:
            logger.debug(f"Cleaned up {len(completed_tasks)} completed tasks")

    def shutdown(self, wait: bool = True):
        """Shutdown executor gracefully.

        Args:
            wait: Wait for running tasks to complete
        """
        logger.info(f"Shutting down BackgroundTaskRunner (wait={wait})")
        self.executor.shutdown(wait=wait)

    def get_active_task_count(self) -> int:
        """Get number of active tasks.

        Returns:
            Count of running tasks
        """
        return len([
            task_id for task_id, future in self.tasks.items()
            if future.running()
        ])


# Global singleton instance
task_runner = BackgroundTaskRunner()
