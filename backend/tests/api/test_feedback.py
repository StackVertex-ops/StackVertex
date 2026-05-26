"""Unit Tests für Feedback API Endpoints."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from io import BytesIO

from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.services.feedback_service import FeedbackService, get_feedback_service
from app.schemas.user import UserResponse


@pytest.fixture
def client():
    """Provide FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_feedback_service():
    """Mock FeedbackService."""
    service = Mock(spec=FeedbackService)
    # Async methods brauchen AsyncMock
    service.submit_feedback = AsyncMock()
    return service


@pytest.fixture
def mock_admin_user():
    """Mock Admin User."""
    from datetime import datetime
    from app.models.user import AuthProvider, UserStatus, SystemRole

    return UserResponse(
        id=uuid4(),
        email="admin@stackvertex.dev",
        name="Admin User",
        auth_provider=AuthProvider.EMAIL,
        status=UserStatus.ACTIVE,
        system_role=SystemRole.SUPERADMIN,
        personal_org_id=uuid4(),
        created_at=datetime.fromisoformat("2026-01-01T00:00:00Z"),
        updated_at=datetime.fromisoformat("2026-01-01T00:00:00Z")
    )


# ============================================================================
# Public Endpoint Tests (No Auth)
# ============================================================================


def test_submit_feedback_minimal(client, mock_feedback_service):
    """Test Feedback einreichen (minimale Daten)."""
    mock_feedback_service.submit_feedback.return_value = {
        "feedback_id": "test-id",
        "type": "bug",
        "status": "new",
        "title": "Button kaputt",
        "description": "Der Submit-Button funktioniert nicht.",
        "email": None,
        "url": None,
        "user_agent": None,
        "browser_info": None,
        "screenshot_s3_key": None,
        "screenshot_url": None,
        "is_resolved": False,
        "resolved_at": None,
        "resolved_by": None,
        "notes": [],
        "created_at": "2026-05-19T10:00:00Z",
        "updated_at": "2026-05-19T10:00:00Z"
    }

    # Override dependency
    app.dependency_overrides[get_feedback_service] = lambda: mock_feedback_service

    response = client.post(
        "/api/v1/feedback",
        data={
            "type": "bug",
            "title": "Button kaputt",
            "description": "Der Submit-Button funktioniert nicht."
        }
    )

    # Cleanup
    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["feedback_id"] == "test-id"
    assert data["type"] == "bug"
    assert data["title"] == "Button kaputt"


def test_submit_feedback_with_email(client, mock_feedback_service):
    """Test Feedback mit Email."""
    mock_feedback_service.submit_feedback.return_value = {
        "feedback_id": "test-id",
        "type": "feature",
        "status": "new",
        "title": "Dark Mode",
        "description": "Bitte Dark Mode hinzufügen",
        "email": "user@example.com",
        "url": None,
        "user_agent": None,
        "browser_info": None,
        "screenshot_s3_key": None,
        "screenshot_url": None,
        "is_resolved": False,
        "resolved_at": None,
        "resolved_by": None,
        "notes": [],
        "created_at": "2026-05-19T10:00:00Z",
        "updated_at": "2026-05-19T10:00:00Z"
    }

    app.dependency_overrides[get_feedback_service] = lambda: mock_feedback_service

    response = client.post(
        "/api/v1/feedback",
        data={
            "type": "feature",
            "title": "Dark Mode",
            "description": "Bitte Dark Mode hinzufügen",
            "email": "user@example.com"
        }
    )

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "user@example.com"


def test_submit_feedback_with_screenshot(client, mock_feedback_service):
    """Test Feedback mit Screenshot-Upload."""
    mock_feedback_service.submit_feedback.return_value = {
        "feedback_id": "test-id",
        "type": "bug",
        "status": "new",
        "title": "UI Error",
        "description": "Layout is broken",
        "email": None,
        "url": None,
        "user_agent": None,
        "browser_info": None,
        "screenshot_s3_key": "feedback/screenshots/2026/05/19/error.png",
        "screenshot_url": None,
        "is_resolved": False,
        "resolved_at": None,
        "resolved_by": None,
        "notes": [],
        "created_at": "2026-05-19T10:00:00Z",
        "updated_at": "2026-05-19T10:00:00Z"
    }

    app.dependency_overrides[get_feedback_service] = lambda: mock_feedback_service

    # Create fake image file
    fake_image = BytesIO(b"fake image content")

    response = client.post(
        "/api/v1/feedback",
        data={
            "type": "bug",
            "title": "UI Error",
            "description": "Layout is broken"
        },
        files={
            "screenshot": ("error.png", fake_image, "image/png")
        }
    )

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["screenshot_s3_key"] == "feedback/screenshots/2026/05/19/error.png"


def test_submit_feedback_invalid_type(client):
    """Test Feedback mit ungültigem Type."""
    response = client.post(
        "/api/v1/feedback",
        data={
            "type": "invalid-type",
            "title": "Test",
            "description": "Test description"
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid type" in response.json()["detail"]


def test_submit_feedback_title_too_short(client):
    """Test Feedback mit zu kurzem Titel."""
    response = client.post(
        "/api/v1/feedback",
        data={
            "type": "bug",
            "title": "Hi",  # Too short (< 5 chars)
            "description": "Test description that is long enough"
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Title must be between" in response.json()["detail"]


def test_submit_feedback_description_too_short(client):
    """Test Feedback mit zu kurzer Beschreibung."""
    response = client.post(
        "/api/v1/feedback",
        data={
            "type": "bug",
            "title": "Valid Title",
            "description": "Short"  # Too short (< 10 chars)
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Description must be between" in response.json()["detail"]


def test_submit_feedback_screenshot_invalid_type(client):
    """Test Feedback mit ungültigem Screenshot-Typ."""
    fake_file = BytesIO(b"fake content")

    response = client.post(
        "/api/v1/feedback",
        data={
            "type": "bug",
            "title": "Valid Title",
            "description": "Valid description here"
        },
        files={
            "screenshot": ("document.pdf", fake_file, "application/pdf")
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid screenshot type" in response.json()["detail"]


def test_submit_feedback_screenshot_too_large(client):
    """Test Feedback mit zu großem Screenshot (> 5MB)."""
    # Create fake file > 5MB
    large_file = BytesIO(b"x" * (6 * 1024 * 1024))

    response = client.post(
        "/api/v1/feedback",
        data={
            "type": "bug",
            "title": "Valid Title",
            "description": "Valid description here"
        },
        files={
            "screenshot": ("large.png", large_file, "image/png")
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Screenshot too large" in response.json()["detail"]


# ============================================================================
# Admin Endpoint Tests (Auth Required)
# ============================================================================


def test_list_feedback_admin(client, mock_feedback_service, mock_admin_user):
    """Test Feedback-Liste abrufen (Admin)."""
    mock_feedback_service.list_feedback.return_value = (
        [
            {
                "feedback_id": "1",
                "type": "bug",
                "status": "new",
                "title": "Bug 1",
                "description": "Description 1",
                "email": None,
                "url": None,
                "user_agent": None,
                "browser_info": None,
                "screenshot_s3_key": None,
                "screenshot_url": None,
                "is_resolved": False,
                "resolved_at": None,
                "resolved_by": None,
                "notes": [],
                "created_at": "2026-05-19T10:00:00Z",
                "updated_at": "2026-05-19T10:00:00Z"
            }
        ],
        None
    )

    # Override dependencies
    from app.api.auth import get_current_superadmin
    app.dependency_overrides[get_feedback_service] = lambda: mock_feedback_service
    app.dependency_overrides[get_current_superadmin] = lambda: mock_admin_user

    response = client.get("/api/v1/feedback")

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == 1


def test_list_feedback_with_filters(client, mock_feedback_service, mock_admin_user):
    """Test Feedback-Liste mit Filtern."""
    mock_feedback_service.list_feedback.return_value = ([], None)

    from app.api.auth import get_current_superadmin
    app.dependency_overrides[get_feedback_service] = lambda: mock_feedback_service
    app.dependency_overrides[get_current_superadmin] = lambda: mock_admin_user

    response = client.get(
        "/api/v1/feedback",
        params={
            "status": "in_progress",
            "type": "bug",
            "limit": 50
        }
    )

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK

    # Verify service was called with filters
    mock_feedback_service.list_feedback.assert_called_once_with(
        status="in_progress",
        feedback_type="bug",
        limit=50
    )


def test_get_feedback_detail_admin(client, mock_feedback_service, mock_admin_user):
    """Test Feedback-Detail abrufen (Admin)."""
    mock_feedback_service.get_feedback.return_value = {
        "feedback_id": "test-id",
        "type": "bug",
        "status": "new",
        "title": "Test Bug",
        "description": "Test description",
        "email": None,
        "url": None,
        "user_agent": None,
        "browser_info": None,
        "screenshot_s3_key": None,
        "screenshot_url": None,
        "is_resolved": False,
        "resolved_at": None,
        "resolved_by": None,
        "notes": [],
        "created_at": "2026-05-19T10:00:00Z",
        "updated_at": "2026-05-19T10:00:00Z"
    }

    from app.api.auth import get_current_superadmin
    app.dependency_overrides[get_feedback_service] = lambda: mock_feedback_service
    app.dependency_overrides[get_current_superadmin] = lambda: mock_admin_user

    response = client.get("/api/v1/feedback/test-id")

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["feedback_id"] == "test-id"


def test_get_feedback_detail_not_found(client, mock_feedback_service, mock_admin_user):
    """Test Feedback-Detail für nicht-existierendes Feedback."""
    mock_feedback_service.get_feedback.return_value = None

    from app.api.auth import get_current_superadmin
    app.dependency_overrides[get_feedback_service] = lambda: mock_feedback_service
    app.dependency_overrides[get_current_superadmin] = lambda: mock_admin_user

    response = client.get("/api/v1/feedback/non-existent-id")

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_feedback_status_admin(client, mock_feedback_service, mock_admin_user):
    """Test Feedback-Status ändern (Admin)."""
    mock_feedback_service.update_feedback_status.return_value = {
        "feedback_id": "test-id",
        "type": "bug",
        "status": "in_progress",
        "title": "Test Bug",
        "description": "Test description",
        "email": None,
        "url": None,
        "user_agent": None,
        "browser_info": None,
        "screenshot_s3_key": None,
        "screenshot_url": None,
        "is_resolved": False,
        "resolved_at": None,
        "resolved_by": None,
        "notes": [],
        "created_at": "2026-05-19T10:00:00Z",
        "updated_at": "2026-05-19T10:00:00Z"
    }

    from app.api.auth import get_current_superadmin
    app.dependency_overrides[get_feedback_service] = lambda: mock_feedback_service
    app.dependency_overrides[get_current_superadmin] = lambda: mock_admin_user

    response = client.patch(
        "/api/v1/feedback/test-id",
        json={
            "status": "in_progress",
            "note": "Working on it"
        }
    )

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "in_progress"


def test_update_feedback_status_invalid_status(client, mock_admin_user):
    """Test Feedback-Status mit ungültigem Status."""
    from app.api.auth import get_current_superadmin
    app.dependency_overrides[get_current_superadmin] = lambda: mock_admin_user

    response = client.patch(
        "/api/v1/feedback/test-id",
        json={
            "status": "invalid-status"
        }
    )

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid status" in response.json()["detail"]


def test_add_note_admin(client, mock_feedback_service, mock_admin_user):
    """Test Notiz zu Feedback hinzufügen (Admin)."""
    mock_feedback_service.add_note.return_value = {
        "feedback_id": "test-id",
        "type": "bug",
        "status": "new",
        "title": "Test Bug",
        "description": "Test description",
        "email": None,
        "url": None,
        "user_agent": None,
        "browser_info": None,
        "screenshot_s3_key": None,
        "screenshot_url": None,
        "is_resolved": False,
        "resolved_at": None,
        "resolved_by": None,
        "notes": [
            {
                "note_id": "note-1",
                "admin_id": str(mock_admin_user.id),
                "admin_email": "admin@stackvertex.dev",
                "note": "Looking into this",
                "created_at": "2026-05-19T10:00:00Z"
            }
        ],
        "created_at": "2026-05-19T10:00:00Z",
        "updated_at": "2026-05-19T10:00:00Z"
    }

    from app.api.auth import get_current_superadmin
    app.dependency_overrides[get_feedback_service] = lambda: mock_feedback_service
    app.dependency_overrides[get_current_superadmin] = lambda: mock_admin_user

    response = client.post(
        "/api/v1/feedback/test-id/notes",
        json={
            "note": "Looking into this"
        }
    )

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["notes"]) == 1
    assert data["notes"][0]["note"] == "Looking into this"


def test_resolve_feedback_admin(client, mock_feedback_service, mock_admin_user):
    """Test Feedback als resolved markieren (Admin)."""
    mock_feedback_service.resolve_feedback.return_value = {
        "feedback_id": "test-id",
        "type": "bug",
        "status": "resolved",
        "title": "Test Bug",
        "description": "Test description",
        "email": None,
        "url": None,
        "user_agent": None,
        "browser_info": None,
        "screenshot_s3_key": None,
        "screenshot_url": None,
        "is_resolved": True,
        "resolved_at": "2026-05-19T11:00:00Z",
        "resolved_by": str(mock_admin_user.id),
        "notes": [
            {
                "note": "✅ RESOLVED: Fixed in v1.2.0"
            }
        ],
        "created_at": "2026-05-19T10:00:00Z",
        "updated_at": "2026-05-19T11:00:00Z"
    }

    from app.api.auth import get_current_superadmin
    app.dependency_overrides[get_feedback_service] = lambda: mock_feedback_service
    app.dependency_overrides[get_current_superadmin] = lambda: mock_admin_user

    response = client.post(
        "/api/v1/feedback/test-id/resolve",
        json={
            "resolution_note": "Fixed in v1.2.0"
        }
    )

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "resolved"
    assert data["is_resolved"] is True


def test_get_stats_admin(client, mock_feedback_service, mock_admin_user):
    """Test Statistiken abrufen (Admin)."""
    mock_feedback_service.get_stats.return_value = {
        "total": 10,
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
        },
        "unresolved": 7
    }

    from app.api.auth import get_current_superadmin
    app.dependency_overrides[get_feedback_service] = lambda: mock_feedback_service
    app.dependency_overrides[get_current_superadmin] = lambda: mock_admin_user

    response = client.get("/api/v1/feedback-stats")

    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 10
    assert data["unresolved"] == 7
    assert data["by_status"]["new"] == 5
    assert data["by_type"]["bug"] == 6


def test_unauthorized_access_to_admin_endpoints(client):
    """Test dass Admin-Endpoints ohne Auth 401 zurückgeben."""
    # GET /feedback (list)
    response = client.get("/api/v1/feedback")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # GET /feedback/{id} (detail)
    response = client.get("/api/v1/feedback/test-id")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # PATCH /feedback/{id} (update status)
    response = client.patch(
        "/api/v1/feedback/test-id",
        json={"status": "in_progress"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # POST /feedback/{id}/notes (add note)
    response = client.post(
        "/api/v1/feedback/test-id/notes",
        json={"note": "Test note"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # POST /feedback/{id}/resolve (resolve)
    response = client.post(
        "/api/v1/feedback/test-id/resolve",
        json={"resolution_note": "Fixed"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # GET /feedback-stats (stats)
    response = client.get("/api/v1/feedback-stats")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
