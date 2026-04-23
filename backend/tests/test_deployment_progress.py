"""Tests für Deployment Progress Tracking.

Testet Progress Calculation und Estimations.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from uuid import uuid4

from app.models.deployment import DeploymentStatus
from app.services.deployment_progress import (
    get_progress_info,
    STATUS_PROGRESS_MAP,
    STATUS_STEP_MAP,
)


class TestDeploymentProgress:
    """Tests für Deployment Progress."""

    def test_progress_pending(self):
        """Test: Progress für PENDING Status."""
        deployment = Mock()
        deployment.status = DeploymentStatus.PENDING
        deployment.started_at = datetime.utcnow()
        deployment.completed_at = None
        deployment.is_running = False

        progress = get_progress_info(deployment)

        assert progress["progress_percentage"] == 0
        assert progress["current_step"] == "Waiting to start"
        assert progress["elapsed_seconds"] >= 0

    def test_progress_generating(self):
        """Test: Progress für GENERATING Status."""
        deployment = Mock()
        deployment.status = DeploymentStatus.GENERATING
        deployment.started_at = datetime.utcnow() - timedelta(seconds=5)
        deployment.completed_at = None
        deployment.is_running = True

        progress = get_progress_info(deployment)

        assert progress["progress_percentage"] == 10
        assert "Generating" in progress["current_step"]
        assert progress["elapsed_seconds"] >= 5
        assert progress["estimated_remaining_seconds"] is not None

    def test_progress_applying(self):
        """Test: Progress für APPLYING Status."""
        deployment = Mock()
        deployment.status = DeploymentStatus.APPLYING
        deployment.started_at = datetime.utcnow() - timedelta(seconds=30)
        deployment.completed_at = None
        deployment.is_running = True

        progress = get_progress_info(deployment)

        assert progress["progress_percentage"] == 60
        assert "Applying" in progress["current_step"]
        assert progress["elapsed_seconds"] >= 30
        assert progress["estimated_remaining_seconds"] is not None

    def test_progress_success(self):
        """Test: Progress für SUCCESS Status."""
        start_time = datetime.utcnow() - timedelta(seconds=120)
        end_time = datetime.utcnow()

        deployment = Mock()
        deployment.status = DeploymentStatus.SUCCESS
        deployment.started_at = start_time
        deployment.completed_at = end_time
        deployment.is_running = False

        progress = get_progress_info(deployment)

        assert progress["progress_percentage"] == 100
        assert "completed successfully" in progress["current_step"]
        assert progress["elapsed_seconds"] >= 120
        assert progress["estimated_remaining_seconds"] is None

    def test_progress_failed(self):
        """Test: Progress für FAILED Status."""
        deployment = Mock()
        deployment.status = DeploymentStatus.FAILED
        deployment.started_at = datetime.utcnow() - timedelta(seconds=60)
        deployment.completed_at = datetime.utcnow()
        deployment.is_running = False

        progress = get_progress_info(deployment)

        assert progress["progress_percentage"] == 100
        assert "failed" in progress["current_step"].lower()
        assert progress["estimated_remaining_seconds"] is None

    def test_progress_cancelled(self):
        """Test: Progress für CANCELLED Status."""
        deployment = Mock()
        deployment.status = DeploymentStatus.CANCELLED
        deployment.started_at = datetime.utcnow() - timedelta(seconds=10)
        deployment.completed_at = datetime.utcnow()
        deployment.is_running = False

        progress = get_progress_info(deployment)

        assert progress["progress_percentage"] == 100
        assert "cancelled" in progress["current_step"].lower()

    def test_all_statuses_have_progress_mapping(self):
        """Test: Alle Status haben Progress Mapping."""
        for status in DeploymentStatus:
            assert status in STATUS_PROGRESS_MAP
            assert status in STATUS_STEP_MAP

    def test_elapsed_time_calculation(self):
        """Test: Elapsed Time korrekt berechnet."""
        start_time = datetime.utcnow() - timedelta(seconds=42)

        deployment = Mock()
        deployment.status = DeploymentStatus.PLANNING
        deployment.started_at = start_time
        deployment.completed_at = None
        deployment.is_running = True

        progress = get_progress_info(deployment)

        # Should be approximately 42 seconds
        assert 40 <= progress["elapsed_seconds"] <= 45

    def test_estimated_remaining_decreases_with_progress(self):
        """Test: Geschätzte Zeit sinkt mit Fortschritt."""
        deployment = Mock()
        deployment.is_running = True
        deployment.started_at = datetime.utcnow()
        deployment.completed_at = None

        # PENDING → longer estimate
        deployment.status = DeploymentStatus.PENDING
        progress_pending = get_progress_info(deployment)

        # PLANNING → shorter estimate
        deployment.status = DeploymentStatus.PLANNING
        progress_planning = get_progress_info(deployment)

        assert progress_pending["estimated_remaining_seconds"] > progress_planning["estimated_remaining_seconds"]

    def test_no_estimate_for_completed_deployments(self):
        """Test: Keine Schätzung für abgeschlossene Deployments."""
        deployment = Mock()
        deployment.status = DeploymentStatus.SUCCESS
        deployment.started_at = datetime.utcnow() - timedelta(seconds=100)
        deployment.completed_at = datetime.utcnow()
        deployment.is_running = False

        progress = get_progress_info(deployment)

        assert progress["estimated_remaining_seconds"] is None

    def test_progress_percentage_range(self):
        """Test: Progress Percentage immer zwischen 0 und 100."""
        for status in DeploymentStatus:
            deployment = Mock()
            deployment.status = status
            deployment.started_at = datetime.utcnow()
            deployment.completed_at = None if status not in [
                DeploymentStatus.SUCCESS,
                DeploymentStatus.FAILED,
                DeploymentStatus.DESTROYED,
                DeploymentStatus.CANCELLED
            ] else datetime.utcnow()
            deployment.is_running = status in [
                DeploymentStatus.GENERATING,
                DeploymentStatus.INITIALIZING,
                DeploymentStatus.PLANNING,
                DeploymentStatus.APPLYING,
                DeploymentStatus.DESTROYING
            ]

            progress = get_progress_info(deployment)

            assert 0 <= progress["progress_percentage"] <= 100
