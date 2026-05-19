"""Unit Tests für Feedback Service."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from io import BytesIO

from fastapi import UploadFile

from app.services.feedback_service import FeedbackService
from app.repositories.feedback import FeedbackRepository
from app.db.s3_storage import S3Storage


@pytest.fixture
def mock_feedback_repo():
    """Mock FeedbackRepository."""
    return Mock(spec=FeedbackRepository)


@pytest.fixture
def mock_s3_storage():
    """Mock S3Storage."""
    mock = Mock()
    # Configure default return values
    mock.put_object = Mock(return_value=None)
    mock.generate_presigned_url = Mock(return_value="https://s3.amazonaws.com/presigned-url")
    return mock


@pytest.fixture
def feedback_service(mock_feedback_repo, mock_s3_storage):
    """Create FeedbackService with mocked dependencies."""
    return FeedbackService(
        feedback_repo=mock_feedback_repo,
        s3_storage=mock_s3_storage
    )


# ============================================================================
# Submit Feedback Tests
# ============================================================================


@pytest.mark.asyncio
async def test_submit_feedback_minimal(feedback_service, mock_feedback_repo):
    """Test Feedback einreichen ohne Screenshot."""
    mock_feedback_repo.create_feedback.return_value = {
        "feedback_id": "test-id",
        "type": "bug",
        "title": "Test Bug",
        "description": "Test description",
        "status": "new"
    }

    feedback = await feedback_service.submit_feedback(
        feedback_type="bug",
        title="Test Bug",
        description="Test description"
    )

    # Verify repository was called correctly
    mock_feedback_repo.create_feedback.assert_called_once_with(
        feedback_type="bug",
        title="Test Bug",
        description="Test description",
        email=None,
        url=None,
        user_agent=None,
        browser_info=None,
        screenshot_s3_key=None
    )

    assert feedback["feedback_id"] == "test-id"
    assert feedback["type"] == "bug"


@pytest.mark.asyncio
async def test_submit_feedback_with_email(feedback_service, mock_feedback_repo):
    """Test Feedback mit Email."""
    mock_feedback_repo.create_feedback.return_value = {
        "feedback_id": "test-id",
        "type": "feature",
        "email": "user@example.com"
    }

    await feedback_service.submit_feedback(
        feedback_type="feature",
        title="Feature Request",
        description="Please add dark mode",
        email="user@example.com"
    )

    # Verify email was passed
    call_kwargs = mock_feedback_repo.create_feedback.call_args.kwargs
    assert call_kwargs["email"] == "user@example.com"


@pytest.mark.asyncio
async def test_submit_feedback_with_browser_info(feedback_service, mock_feedback_repo):
    """Test Feedback mit Browser-Info."""
    browser_info = {
        "browser": "Chrome",
        "version": "120.0.0"
    }

    mock_feedback_repo.create_feedback.return_value = {
        "feedback_id": "test-id",
        "type": "bug"
    }

    await feedback_service.submit_feedback(
        feedback_type="bug",
        title="Layout broken",
        description="Layout issue",
        url="https://app.overcloud.dev/dashboard",
        user_agent="Mozilla/5.0 ...",
        browser_info=browser_info
    )

    # Verify browser info was passed
    call_kwargs = mock_feedback_repo.create_feedback.call_args.kwargs
    assert call_kwargs["url"] == "https://app.overcloud.dev/dashboard"
    assert call_kwargs["user_agent"] == "Mozilla/5.0 ..."
    assert call_kwargs["browser_info"] == browser_info


@pytest.mark.asyncio
async def test_submit_feedback_with_screenshot(feedback_service, mock_feedback_repo, mock_s3_storage):
    """Test Feedback mit Screenshot-Upload."""
    # Mock S3 upload
    mock_s3_storage.put_object.return_value = None

    # Create mock UploadFile with content_type
    file_content = b"fake image content"
    # Mock UploadFile completely
    screenshot = Mock(spec=UploadFile)
    screenshot.filename = "error-screenshot.png"
    screenshot.content_type = "image/png"
    screenshot.read = AsyncMock(return_value=file_content)

    mock_feedback_repo.create_feedback.return_value = {
        "feedback_id": "test-id",
        "screenshot_s3_key": "feedback/screenshots/2026/05/19/error-screenshot.png"
    }

    feedback = await feedback_service.submit_feedback(
        feedback_type="bug",
        title="UI Error",
        description="Error on screen",
        screenshot=screenshot
    )

    # Verify S3 upload was called
    mock_s3_storage.put_object.assert_called_once()
    call_args = mock_s3_storage.put_object.call_args
    assert "feedback/screenshots/" in call_args.kwargs["key"]
    assert call_args.kwargs["content_type"] == "image/png"

    # Verify repository was called with S3 key
    call_kwargs = mock_feedback_repo.create_feedback.call_args.kwargs
    assert call_kwargs["screenshot_s3_key"] is not None
    assert "feedback/screenshots/" in call_kwargs["screenshot_s3_key"]


# ============================================================================
# Get Feedback Tests
# ============================================================================


def test_get_feedback_without_screenshot(feedback_service, mock_feedback_repo):
    """Test Feedback abrufen ohne Screenshot."""
    mock_feedback_repo.get_feedback.return_value = {
        "feedback_id": "test-id",
        "type": "bug",
        "screenshot_s3_key": None
    }

    feedback = feedback_service.get_feedback("test-id")

    assert feedback is not None
    assert feedback["feedback_id"] == "test-id"
    assert "screenshot_url" not in feedback


def test_get_feedback_with_screenshot(feedback_service, mock_feedback_repo, mock_s3_storage):
    """Test Feedback abrufen mit Screenshot (presigned URL)."""
    mock_feedback_repo.get_feedback.return_value = {
        "feedback_id": "test-id",
        "type": "bug",
        "screenshot_s3_key": "feedback/screenshots/2026/05/19/error.png"
    }

    mock_s3_storage.generate_presigned_url.return_value = "https://s3.amazonaws.com/presigned-url"

    feedback = feedback_service.get_feedback("test-id")

    # Verify presigned URL was generated
    mock_s3_storage.generate_presigned_url.assert_called_once_with(
        key="feedback/screenshots/2026/05/19/error.png",
        expiration=3600
    )

    assert feedback["screenshot_url"] == "https://s3.amazonaws.com/presigned-url"


def test_get_feedback_not_found(feedback_service, mock_feedback_repo):
    """Test Feedback nicht gefunden."""
    mock_feedback_repo.get_feedback.return_value = None

    feedback = feedback_service.get_feedback("non-existent-id")

    assert feedback is None


# ============================================================================
# List Feedback Tests
# ============================================================================


def test_list_feedback_all(feedback_service, mock_feedback_repo):
    """Test Feedback-Liste abrufen."""
    mock_feedback_repo.list_feedback.return_value = (
        [
            {"feedback_id": "1", "screenshot_s3_key": None},
            {"feedback_id": "2", "screenshot_s3_key": None}
        ],
        None
    )

    items, last_key = feedback_service.list_feedback()

    assert len(items) == 2
    assert last_key is None


def test_list_feedback_with_screenshots(feedback_service, mock_feedback_repo, mock_s3_storage):
    """Test Feedback-Liste mit Screenshots (presigned URLs)."""
    mock_feedback_repo.list_feedback.return_value = (
        [
            {
                "feedback_id": "1",
                "screenshot_s3_key": "feedback/screenshots/1.png"
            },
            {
                "feedback_id": "2",
                "screenshot_s3_key": None
            },
            {
                "feedback_id": "3",
                "screenshot_s3_key": "feedback/screenshots/3.png"
            }
        ],
        None
    )

    mock_s3_storage.generate_presigned_url.return_value = "https://s3.amazonaws.com/presigned-url"

    items, _ = feedback_service.list_feedback()

    # Verify presigned URLs were generated for items with screenshots
    assert mock_s3_storage.generate_presigned_url.call_count == 2
    assert items[0]["screenshot_url"] is not None
    assert "screenshot_url" not in items[1]  # No screenshot
    assert items[2]["screenshot_url"] is not None


def test_list_feedback_with_filters(feedback_service, mock_feedback_repo):
    """Test Feedback-Liste mit Filtern."""
    mock_feedback_repo.list_feedback.return_value = ([], None)

    feedback_service.list_feedback(
        status="in_progress",
        feedback_type="bug",
        limit=50
    )

    # Verify filters were passed to repository
    mock_feedback_repo.list_feedback.assert_called_once_with(
        status="in_progress",
        feedback_type="bug",
        limit=50,
        last_evaluated_key=None
    )


# ============================================================================
# Update Feedback Status Tests
# ============================================================================


def test_update_feedback_status_without_note(feedback_service, mock_feedback_repo):
    """Test Feedback-Status ändern ohne Notiz."""
    mock_feedback_repo.update_feedback.return_value = {
        "feedback_id": "test-id",
        "status": "in_progress"
    }

    feedback = feedback_service.update_feedback_status(
        feedback_id="test-id",
        admin_id="admin-123",
        admin_email="admin@overcloud.dev",
        status="in_progress"
    )

    # Verify status update was called
    mock_feedback_repo.update_feedback.assert_called_once_with(
        feedback_id="test-id",
        status="in_progress"
    )

    # Verify no note was added
    mock_feedback_repo.add_note.assert_not_called()

    assert feedback["status"] == "in_progress"


def test_update_feedback_status_with_note(feedback_service, mock_feedback_repo):
    """Test Feedback-Status ändern mit Notiz."""
    mock_feedback_repo.update_feedback.return_value = {
        "feedback_id": "test-id",
        "status": "in_progress"
    }

    mock_feedback_repo.add_note.return_value = {
        "feedback_id": "test-id",
        "status": "in_progress",
        "notes": [{"note": "Working on it"}]
    }

    feedback = feedback_service.update_feedback_status(
        feedback_id="test-id",
        admin_id="admin-123",
        admin_email="admin@overcloud.dev",
        status="in_progress",
        note="Working on it"
    )

    # Verify status update was called
    mock_feedback_repo.update_feedback.assert_called_once()

    # Verify note was added
    mock_feedback_repo.add_note.assert_called_once_with(
        feedback_id="test-id",
        admin_id="admin-123",
        admin_email="admin@overcloud.dev",
        note="Working on it"
    )

    assert len(feedback["notes"]) == 1


def test_update_feedback_status_not_found(feedback_service, mock_feedback_repo):
    """Test Status-Update für nicht-existierendes Feedback."""
    mock_feedback_repo.update_feedback.return_value = None

    feedback = feedback_service.update_feedback_status(
        feedback_id="non-existent-id",
        admin_id="admin-123",
        admin_email="admin@overcloud.dev",
        status="closed"
    )

    assert feedback is None


# ============================================================================
# Add Note Tests
# ============================================================================


def test_add_note(feedback_service, mock_feedback_repo):
    """Test Notiz zu Feedback hinzufügen."""
    mock_feedback_repo.add_note.return_value = {
        "feedback_id": "test-id",
        "notes": [
            {
                "note_id": "note-1",
                "admin_email": "admin@overcloud.dev",
                "note": "Looking into this"
            }
        ]
    }

    feedback = feedback_service.add_note(
        feedback_id="test-id",
        admin_id="admin-123",
        admin_email="admin@overcloud.dev",
        note="Looking into this"
    )

    # Verify repository was called
    mock_feedback_repo.add_note.assert_called_once_with(
        feedback_id="test-id",
        admin_id="admin-123",
        admin_email="admin@overcloud.dev",
        note="Looking into this"
    )

    assert len(feedback["notes"]) == 1


def test_add_note_not_found(feedback_service, mock_feedback_repo):
    """Test Notiz zu nicht-existierendem Feedback."""
    mock_feedback_repo.add_note.return_value = None

    feedback = feedback_service.add_note(
        feedback_id="non-existent-id",
        admin_id="admin-123",
        admin_email="admin@overcloud.dev",
        note="This should fail"
    )

    assert feedback is None


# ============================================================================
# Resolve Feedback Tests
# ============================================================================


def test_resolve_feedback(feedback_service, mock_feedback_repo):
    """Test Feedback als resolved markieren."""
    mock_feedback_repo.mark_resolved.return_value = {
        "feedback_id": "test-id",
        "status": "resolved",
        "is_resolved": True,
        "notes": [
            {
                "note": "✅ RESOLVED: Fixed in v1.2.0"
            }
        ]
    }

    feedback = feedback_service.resolve_feedback(
        feedback_id="test-id",
        admin_id="admin-123",
        admin_email="admin@overcloud.dev",
        resolution_note="Fixed in v1.2.0"
    )

    # Verify repository was called
    mock_feedback_repo.mark_resolved.assert_called_once_with(
        feedback_id="test-id",
        admin_id="admin-123",
        admin_email="admin@overcloud.dev",
        resolution_note="Fixed in v1.2.0"
    )

    assert feedback["status"] == "resolved"
    assert feedback["is_resolved"] is True


def test_resolve_feedback_not_found(feedback_service, mock_feedback_repo):
    """Test resolve für nicht-existierendes Feedback."""
    mock_feedback_repo.mark_resolved.return_value = None

    feedback = feedback_service.resolve_feedback(
        feedback_id="non-existent-id",
        admin_id="admin-123",
        admin_email="admin@overcloud.dev",
        resolution_note="This should fail"
    )

    assert feedback is None


# ============================================================================
# Statistics Tests
# ============================================================================


def test_get_stats(feedback_service, mock_feedback_repo):
    """Test Statistiken abrufen."""
    mock_feedback_repo.get_stats.return_value = {
        "total": 10,
        "unresolved": 7,
        "by_status": {
            "new": 5,
            "in_progress": 2,
            "resolved": 3,
            "closed": 0
        },
        "by_type": {
            "bug": 6,
            "feature": 3,
            "feedback": 1,
            "other": 0
        }
    }

    stats = feedback_service.get_stats()

    # Verify repository was called
    mock_feedback_repo.get_stats.assert_called_once()

    assert stats["total"] == 10
    assert stats["unresolved"] == 7
    assert stats["by_status"]["new"] == 5
    assert stats["by_type"]["bug"] == 6
