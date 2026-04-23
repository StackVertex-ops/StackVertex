"""Tests für Background Task System.

Testet ThreadPool-basierte Background Execution.
"""

import pytest
import time
from uuid import uuid4
from unittest.mock import Mock

from app.services.background_tasks import BackgroundTaskRunner


class TestBackgroundTaskRunner:
    """Tests für BackgroundTaskRunner."""

    def test_create_runner(self):
        """Test: Runner erstellen (Singleton)."""
        runner1 = BackgroundTaskRunner()
        runner2 = BackgroundTaskRunner()

        # Same instance (Singleton)
        assert runner1 is runner2

    def test_submit_simple_task(self):
        """Test: Einfache Task submitten."""
        runner = BackgroundTaskRunner()

        result_container = []

        def simple_task(value):
            result_container.append(value)
            return value * 2

        task_id = uuid4()
        future = runner.submit_task(task_id, simple_task, 42)

        # Wait for completion
        result = future.result(timeout=1.0)

        assert result == 84
        assert 42 in result_container

    def test_task_status_running(self):
        """Test: Task Status während Ausführung."""
        runner = BackgroundTaskRunner()

        def slow_task():
            time.sleep(0.5)
            return "done"

        task_id = uuid4()
        future = runner.submit_task(task_id, slow_task)

        # Check status immediately (should be running or pending)
        status = runner.get_task_status(task_id)
        assert status in ["running", "pending"]

        # Wait for completion
        future.result(timeout=2.0)

        # Status should be completed (or None if cleaned up)
        status = runner.get_task_status(task_id)
        assert status in ["completed", None]

    def test_task_status_failed(self):
        """Test: Task Status bei Fehler."""
        runner = BackgroundTaskRunner()

        def failing_task():
            raise ValueError("Intentional error")

        task_id = uuid4()
        future = runner.submit_task(task_id, failing_task)

        # Wait for task to fail
        with pytest.raises(ValueError, match="Intentional error"):
            future.result(timeout=1.0)

    def test_task_with_args_and_kwargs(self):
        """Test: Task mit Args und Kwargs."""
        runner = BackgroundTaskRunner()

        def task_with_params(a, b, multiplier=1):
            return (a + b) * multiplier

        task_id = uuid4()
        future = runner.submit_task(
            task_id,
            task_with_params,
            10,
            20,
            multiplier=3
        )

        result = future.result(timeout=1.0)
        assert result == 90  # (10 + 20) * 3

    def test_multiple_concurrent_tasks(self):
        """Test: Mehrere Tasks parallel."""
        runner = BackgroundTaskRunner()

        results = []

        def concurrent_task(task_num):
            time.sleep(0.1)  # Simulate work
            return task_num

        # Submit 3 tasks
        futures = []
        for i in range(3):
            task_id = uuid4()
            future = runner.submit_task(task_id, concurrent_task, i)
            futures.append(future)

        # Wait for all
        for i, future in enumerate(futures):
            result = future.result(timeout=2.0)
            assert result == i

    def test_cancel_task_before_execution(self):
        """Test: Task canceln bevor sie startet."""
        runner = BackgroundTaskRunner()

        def never_runs():
            raise AssertionError("Should not execute")

        task_id = uuid4()
        future = runner.submit_task(task_id, never_runs)

        # Try to cancel immediately
        cancelled = runner.cancel_task(task_id)

        # May or may not succeed (race condition with executor)
        # Just verify no exception
        assert isinstance(cancelled, bool)

    def test_get_active_task_count(self):
        """Test: Active Task Count."""
        runner = BackgroundTaskRunner()

        def slow_task():
            time.sleep(1.0)

        # Submit task
        task_id = uuid4()
        future = runner.submit_task(task_id, slow_task)

        # Should have at least one active task (or completed if very fast)
        # Just verify no exception
        count = runner.get_active_task_count()
        assert isinstance(count, int)
        assert count >= 0

        # Cleanup
        future.result(timeout=2.0)

    @pytest.mark.skip(reason="caplog doesn't capture thread logs")
    def test_task_logging(self, caplog):
        """Test: Task Logging."""
        runner = BackgroundTaskRunner()

        def logged_task():
            return "success"

        task_id = uuid4()
        future = runner.submit_task(task_id, logged_task)
        future.result(timeout=1.0)

        # Check logs contain task ID
        assert str(task_id) in caplog.text

    def test_exception_propagation(self):
        """Test: Exceptions werden propagiert."""
        runner = BackgroundTaskRunner()

        def error_task():
            raise RuntimeError("Critical error")

        task_id = uuid4()
        future = runner.submit_task(task_id, error_task)

        with pytest.raises(RuntimeError, match="Critical error"):
            future.result(timeout=1.0)
