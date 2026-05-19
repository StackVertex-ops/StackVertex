"""Tests für FAQ API Endpoints.

Testet Public und Admin Endpoints:
- GET /faq (public)
- GET /faq/search (public)
- GET /faq/categories (public)
- GET /faq/{faq_id} (public, mit view tracking)
- GET /admin/faq (SuperAdmin)
- POST /admin/faq (SuperAdmin)
- PATCH /admin/faq/{faq_id} (SuperAdmin)
- DELETE /admin/faq/{faq_id} (SuperAdmin)
- POST /admin/faq/reorder (SuperAdmin)
- GET /admin/faq/analytics (SuperAdmin)
- POST /admin/faq/categories (SuperAdmin)
- PATCH /admin/faq/categories/{category_id} (SuperAdmin)
- DELETE /admin/faq/categories/{category_id} (SuperAdmin)
"""

import pytest
from unittest.mock import patch
from uuid import uuid4

from fastapi import status

from app.models.user import SystemRole, UserStatus


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def superadmin_user():
    """Mock SuperAdmin user für Auth."""
    return {
        "user_id": str(uuid4()),
        "email": "admin@overcloud.io",
        "name": "Super Admin",
        "system_role": SystemRole.SUPERADMIN.value,
        "status": UserStatus.ACTIVE.value,
    }


@pytest.fixture
def authenticated_client(client, superadmin_user):
    """Provide TestClient with mocked SuperAdmin authentication."""
    from app.api.auth import get_current_superadmin
    from app.main import app

    # Override auth dependency
    app.dependency_overrides[get_current_superadmin] = lambda: superadmin_user

    # Attach user to client for access in tests
    client.superadmin_user = superadmin_user

    yield client

    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture
def faq_repository(mock_dynamodb_table):
    """Provide FaqRepository with mocked DynamoDB table."""
    from app.repositories.faq import FaqRepository

    return FaqRepository(table=mock_dynamodb_table)


@pytest.fixture
def setup_categories(faq_repository):
    """Setup standard categories für Tests."""
    categories = [
        {"name": "General", "slug": "general", "icon": "❓", "sort_order": 0},
        {"name": "Pricing", "slug": "pricing", "icon": "💰", "sort_order": 1},
        {"name": "Technical", "slug": "technical", "icon": "🔧", "sort_order": 2},
    ]

    created = []
    for cat_data in categories:
        cat = faq_repository.create_category(**cat_data)
        created.append(cat)

    return created


@pytest.fixture
def setup_faqs(faq_repository, setup_categories):
    """Setup sample FAQs für Tests."""
    faqs_data = [
        # Published FAQs
        {
            "category": "general",
            "question": "Was ist OverCloud?",
            "answer": "OverCloud ist eine Multi-Cloud Platform.",
            "sort_order": 0,
            "status": "published",
        },
        {
            "category": "pricing",
            "question": "Wie viel kostet OverCloud?",
            "answer": "Pricing starts at $10/month.",
            "sort_order": 0,
            "status": "published",
        },
        # Draft FAQ
        {
            "category": "general",
            "question": "Draft FAQ?",
            "answer": "This is a draft.",
            "sort_order": 1,
            "status": "draft",
        },
    ]

    created = []
    for faq_data in faqs_data:
        faq = faq_repository.create_faq(**faq_data)
        created.append(faq)

    return created


# =============================================================================
# Public Endpoints Tests
# =============================================================================


def test_get_faqs_public(client, setup_faqs):
    """Test: GET /faq - Nur published FAQs."""
    response = client.get("/api/v1/faq")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["success"] is True
    assert "data" in data

    result = data["data"]
    assert "categories" in result
    assert result["total"] == 2  # Nur published

    # Prüfe dass drafts nicht enthalten sind
    all_questions = []
    for cat in result["categories"]:
        for faq in cat["faqs"]:
            all_questions.append(faq["question"])

    assert "Draft FAQ?" not in all_questions


def test_get_faqs_by_category(client, setup_faqs):
    """Test: GET /faq?category=pricing - Filter nach Kategorie."""
    response = client.get("/api/v1/faq?category=pricing")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    result = data["data"]

    assert result["category"] == "pricing"
    assert len(result["faqs"]) == 1
    assert result["faqs"][0]["question"] == "Wie viel kostet OverCloud?"


def test_search_faqs(client, setup_faqs):
    """Test: GET /faq/search?q=OverCloud - Suche."""
    response = client.get("/api/v1/faq/search?q=OverCloud")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["success"] is True
    assert data["query"] == "OverCloud"
    assert data["total"] >= 1
    assert len(data["results"]) >= 1

    # Prüfe dass richtige FAQ gefunden wurde
    questions = [faq["question"] for faq in data["results"]]
    assert "Was ist OverCloud?" in questions


def test_search_faqs_case_insensitive(client, setup_faqs):
    """Test: Suche ist case-insensitive."""
    response = client.get("/api/v1/faq/search?q=overcloud")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] >= 1


def test_search_faqs_no_results(client, setup_faqs):
    """Test: Suche ohne Ergebnisse."""
    response = client.get("/api/v1/faq/search?q=xyz123notfound")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["total"] == 0
    assert len(data["results"]) == 0


def test_search_faqs_missing_query(client):
    """Test: Suche ohne Query-Parameter."""
    response = client.get("/api/v1/faq/search")

    # FastAPI Validation Error (Query param required)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_categories(client, setup_categories):
    """Test: GET /faq/categories - Kategorien abrufen."""
    response = client.get("/api/v1/faq/categories")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["success"] is True
    assert "categories" in data
    assert len(data["categories"]) == 3

    # Prüfe Sortierung
    categories = data["categories"]
    assert categories[0]["slug"] == "general"
    assert categories[1]["slug"] == "pricing"
    assert categories[2]["slug"] == "technical"


def test_get_faq_detail(client, faq_repository, setup_faqs):
    """Test: GET /faq/{faq_id} - FAQ Detail mit View-Tracking."""
    faq = setup_faqs[0]
    faq_id = faq["faq_id"]

    # Initial view_count = 0
    assert faq["view_count"] == 0

    # GET Detail
    response = client.get(f"/api/v1/faq/{faq_id}")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["success"] is True
    assert data["data"]["faq_id"] == faq_id
    # DynamoDB speichert Numbers als Decimal/String in JSON response
    assert int(data["data"]["view_count"]) == 1  # Incremented

    # Nochmal abrufen
    response = client.get(f"/api/v1/faq/{faq_id}")
    assert int(response.json()["data"]["view_count"]) == 2


def test_get_faq_detail_draft_not_public(client, setup_faqs):
    """Test: Draft FAQ nicht öffentlich zugänglich."""
    draft_faq = next(faq for faq in setup_faqs if faq["status"] == "draft")
    faq_id = draft_faq["faq_id"]

    response = client.get(f"/api/v1/faq/{faq_id}")

    # Sollte 404 zurückgeben (nicht öffentlich)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_faq_detail_not_found(client):
    """Test: Nicht existierendes FAQ."""
    response = client.get("/api/v1/faq/non-existent-id")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Admin Endpoints Tests - List & Get
# =============================================================================


def test_list_all_faqs_admin(authenticated_client, setup_faqs):
    """Test: GET /admin/faq - Admin sieht alle FAQs (inkl. drafts)."""
    response = authenticated_client.get("/api/v1/admin/faq")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["success"] is True
    assert data["total"] == 3  # 2 published + 1 draft

    # Prüfe dass drafts enthalten sind
    statuses = [faq["status"] for faq in data["faqs"]]
    assert "draft" in statuses


def test_list_all_faqs_admin_filter_status(authenticated_client, setup_faqs):
    """Test: Admin filtert nach Status."""
    response = authenticated_client.get("/api/v1/admin/faq?status=published")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["total"] == 2
    assert all(faq["status"] == "published" for faq in data["faqs"])


def test_list_all_faqs_admin_filter_category(authenticated_client, setup_faqs):
    """Test: Admin filtert nach Kategorie."""
    response = authenticated_client.get("/api/v1/admin/faq?category=general")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["total"] == 2  # 1 published + 1 draft
    assert all(faq["category"] == "general" for faq in data["faqs"])


def test_list_all_faqs_unauthorized(client):
    """Test: Admin-Endpoint ohne Auth = 401."""
    response = client.get("/api/v1/admin/faq")

    # get_current_superadmin dependency sollte 401 werfen
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# Admin Endpoints Tests - Create FAQ
# =============================================================================


def test_create_faq_admin(authenticated_client):
    """Test: POST /admin/faq - FAQ erstellen."""
    request_data = {
        "category": "security",
        "question": "Ist OverCloud sicher?",
        "answer": "Ja, mit End-to-End-Verschlüsselung.",
        "status": "published",
        "sort_order": 0,
    }

    response = authenticated_client.post("/api/v1/admin/faq", json=request_data)

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["success"] is True
    assert data["message"] == "FAQ created successfully"
    assert data["data"]["question"] == request_data["question"]
    assert data["data"]["status"] == "published"
    assert data["data"]["created_by"] == authenticated_client.superadmin_user["user_id"]


def test_create_faq_admin_default_status(authenticated_client):
    """Test: FAQ mit default status=draft."""
    request_data = {
        "category": "general",
        "question": "Test Question?",
        "answer": "Test Answer.",
    }

    response = authenticated_client.post("/api/v1/admin/faq", json=request_data)

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["data"]["status"] == "draft"  # Default
    # DynamoDB speichert Numbers als Decimal
    assert int(data["data"]["sort_order"]) == 0  # Default


def test_create_faq_admin_validation_error(authenticated_client):
    """Test: Validation Error bei ungültigen Daten."""
    request_data = {
        "category": "general",
        "question": "X",  # Too short (min_length=5)
        "answer": "Test.",
    }

    response = authenticated_client.post("/api/v1/admin/faq", json=request_data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_faq_unauthorized(client):
    """Test: Ohne Auth = 401."""
    request_data = {
        "category": "general",
        "question": "Test Question?",
        "answer": "Test Answer.",
    }

    response = client.post("/api/v1/admin/faq", json=request_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# Admin Endpoints Tests - Update FAQ
# =============================================================================


def test_update_faq_admin(authenticated_client, setup_faqs):
    """Test: PATCH /admin/faq/{faq_id} - FAQ updaten."""
    faq = setup_faqs[0]
    faq_id = faq["faq_id"]

    update_data = {
        "question": "Updated Question?",
        "status": "draft",
    }

    response = authenticated_client.patch(f"/api/v1/admin/faq/{faq_id}", json=update_data)

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["success"] is True
    assert data["message"] == "FAQ updated successfully"
    assert data["data"]["question"] == "Updated Question?"
    assert data["data"]["status"] == "draft"
    assert data["data"]["updated_by"] == authenticated_client.superadmin_user["user_id"]


def test_update_faq_admin_partial_update(authenticated_client, setup_faqs):
    """Test: Partial Update (nur ein Feld ändern)."""
    faq = setup_faqs[0]
    faq_id = faq["faq_id"]
    original_question = faq["question"]

    update_data = {
        "status": "draft",
    }

    response = authenticated_client.patch(f"/api/v1/admin/faq/{faq_id}", json=update_data)

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["data"]["status"] == "draft"
    assert data["data"]["question"] == original_question  # Unchanged


def test_update_faq_admin_not_found(authenticated_client):
    """Test: Nicht existierendes FAQ updaten."""
    update_data = {
        "question": "New Question?",
    }

    response = authenticated_client.patch("/api/v1/admin/faq/non-existent-id", json=update_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_faq_admin_no_updates(authenticated_client, setup_faqs):
    """Test: Keine Updates bereitgestellt = 400."""
    faq = setup_faqs[0]
    faq_id = faq["faq_id"]

    update_data = {}  # Leer

    response = authenticated_client.patch(f"/api/v1/admin/faq/{faq_id}", json=update_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_update_faq_unauthorized(client, setup_faqs):
    """Test: Ohne Auth = 401."""
    faq = setup_faqs[0]
    faq_id = faq["faq_id"]

    update_data = {"question": "New Question?"}

    response = client.patch(f"/api/v1/admin/faq/{faq_id}", json=update_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# Admin Endpoints Tests - Delete FAQ
# =============================================================================


def test_delete_faq_admin(authenticated_client, faq_repository, setup_faqs):
    """Test: DELETE /admin/faq/{faq_id} - FAQ löschen."""
    faq = setup_faqs[0]
    faq_id = faq["faq_id"]

    response = authenticated_client.delete(f"/api/v1/admin/faq/{faq_id}")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["success"] is True
    assert data["message"] == "FAQ deleted successfully"

    # Prüfe dass FAQ gelöscht ist
    deleted_faq = faq_repository.get_faq(faq_id)
    assert deleted_faq is None


def test_delete_faq_admin_not_found(authenticated_client):
    """Test: Nicht existierendes FAQ löschen (idempotent)."""
    response = authenticated_client.delete("/api/v1/admin/faq/non-existent-id")

    # DynamoDB delete ist idempotent - gibt 200 zurück auch wenn Item nicht existiert
    # API meldet success=False wenn Item nicht gefunden
    assert response.status_code == status.HTTP_200_OK


def test_delete_faq_unauthorized(client, setup_faqs):
    """Test: Ohne Auth = 401."""
    faq = setup_faqs[0]
    faq_id = faq["faq_id"]

    response = client.delete(f"/api/v1/admin/faq/{faq_id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# Admin Endpoints Tests - Reorder FAQs
# =============================================================================


def test_reorder_faqs_admin(authenticated_client, faq_repository, setup_faqs):
    """Test: POST /admin/faq/reorder - Sortierung ändern."""
    faq1 = setup_faqs[0]
    faq2 = setup_faqs[1]

    # Neue Reihenfolge: 2, 1
    reorder_data = {
        "faq_ids": [faq2["faq_id"], faq1["faq_id"]],
    }

    response = authenticated_client.post("/api/v1/admin/faq/reorder", json=reorder_data)

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["success"] is True
    assert data["message"] == "FAQs reordered successfully"

    # Prüfe neue sort_order
    updated_faq2 = faq_repository.get_faq(faq2["faq_id"])
    updated_faq1 = faq_repository.get_faq(faq1["faq_id"])

    assert updated_faq2["sort_order"] == 0
    assert updated_faq1["sort_order"] == 1


def test_reorder_faqs_admin_empty_list(authenticated_client):
    """Test: Leere FAQ-Liste = Validation Error."""
    reorder_data = {
        "faq_ids": [],
    }

    response = authenticated_client.post("/api/v1/admin/faq/reorder", json=reorder_data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_reorder_faqs_unauthorized(client):
    """Test: Ohne Auth = 401."""
    reorder_data = {
        "faq_ids": ["id1", "id2"],
    }

    response = client.post("/api/v1/admin/faq/reorder", json=reorder_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# Admin Endpoints Tests - Analytics
# =============================================================================


def test_get_analytics_admin(authenticated_client, faq_repository, setup_faqs):
    """Test: GET /admin/faq/analytics - Analytics abrufen."""
    # Setze view_counts
    faq_repository.increment_view_count(setup_faqs[0]["faq_id"])
    faq_repository.increment_view_count(setup_faqs[0]["faq_id"])
    faq_repository.increment_view_count(setup_faqs[1]["faq_id"])

    response = authenticated_client.get("/api/v1/admin/faq/analytics")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["success"] is True
    assert "analytics" in data

    analytics = data["analytics"]
    assert int(analytics["total_faqs"]) == 3
    assert int(analytics["published"]) == 2
    assert int(analytics["drafts"]) == 1
    assert int(analytics["total_views"]) == 3
    assert len(analytics["top_viewed"]) >= 1


def test_get_analytics_unauthorized(client):
    """Test: Ohne Auth = 401."""
    response = client.get("/api/v1/admin/faq/analytics")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# Admin Endpoints Tests - Category Management
# =============================================================================


def test_create_category_admin(authenticated_client):
    """Test: POST /admin/faq/categories - Kategorie erstellen."""
    request_data = {
        "name": "Security",
        "slug": "security",
        "icon": "🔒",
        "sort_order": 99,
    }

    response = authenticated_client.post("/api/v1/admin/faq/categories", json=request_data)

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Category created successfully"
    assert data["data"]["name"] == "Security"
    assert data["data"]["slug"] == "security"
    assert data["data"]["icon"] == "🔒"
    assert data["data"]["sort_order"] == 99


def test_create_category_admin_validation_error(authenticated_client):
    """Test: Validation Error bei ungültigem Slug."""
    request_data = {
        "name": "Test",
        "slug": "INVALID SLUG",  # Muss lowercase + dash sein
        "icon": "",
    }

    response = authenticated_client.post("/api/v1/admin/faq/categories", json=request_data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_category_unauthorized(client):
    """Test: Ohne Auth = 401."""
    request_data = {
        "name": "Security",
        "slug": "security",
    }

    response = client.post("/api/v1/admin/faq/categories", json=request_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_category_admin(authenticated_client, setup_categories):
    """Test: PATCH /admin/faq/categories/{category_id} - Kategorie updaten."""
    category = setup_categories[0]
    category_id = category["category_id"]

    update_data = {
        "name": "Updated General",
        "icon": "🆕",
    }

    response = authenticated_client.patch(
            f"/api/v1/admin/faq/categories/{category_id}",
            json=update_data,
        )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Category updated successfully"
    assert data["data"]["name"] == "Updated General"
    assert data["data"]["icon"] == "🆕"


def test_update_category_admin_not_found(authenticated_client):
    """Test: Nicht existierende Kategorie updaten."""
    update_data = {"name": "New Name"}

    response = authenticated_client.patch(
            "/api/v1/admin/faq/categories/non-existent-id",
            json=update_data,
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_category_admin_no_updates(authenticated_client, setup_categories):
    """Test: Keine Updates = 400."""
    category = setup_categories[0]
    category_id = category["category_id"]

    update_data = {}

    response = authenticated_client.patch(
            f"/api/v1/admin/faq/categories/{category_id}",
            json=update_data,
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_update_category_unauthorized(client, setup_categories):
    """Test: Ohne Auth = 401."""
    category = setup_categories[0]
    category_id = category["category_id"]

    update_data = {"name": "New Name"}

    response = client.patch(
        f"/api/v1/admin/faq/categories/{category_id}",
        json=update_data,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_category_admin(authenticated_client, faq_repository, setup_categories):
    """Test: DELETE /admin/faq/categories/{category_id} - Kategorie löschen."""
    category = setup_categories[0]
    category_id = category["category_id"]

    response = authenticated_client.delete(f"/api/v1/admin/faq/categories/{category_id}")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Category deleted successfully"

    # Prüfe dass Kategorie gelöscht ist
    deleted_category = faq_repository.get_category(category_id)
    assert deleted_category is None


def test_delete_category_admin_not_found(authenticated_client):
    """Test: Nicht existierende Kategorie löschen (idempotent)."""
    response = authenticated_client.delete("/api/v1/admin/faq/categories/non-existent-id")

    # DynamoDB delete ist idempotent - gibt 200 zurück auch wenn Item nicht existiert
    assert response.status_code == status.HTTP_200_OK


def test_delete_category_unauthorized(client, setup_categories):
    """Test: Ohne Auth = 401."""
    category = setup_categories[0]
    category_id = category["category_id"]

    response = client.delete(f"/api/v1/admin/faq/categories/{category_id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
