"""Tests für FAQ Repository.

Testet DynamoDB-Operationen für FAQ Management:
- FAQ CRUD Operations
- Category Management
- Sortierung und Reordering
- View Count Tracking
- Published/Draft Status
- GSI Queries
"""

import pytest
from datetime import datetime
from uuid import uuid4


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def faq_repository(mock_dynamodb_table):
    """Provide FaqRepository with mocked DynamoDB table."""
    from app.repositories.faq import FaqRepository

    return FaqRepository(table=mock_dynamodb_table)


@pytest.fixture
def sample_faq_data():
    """Sample FAQ data für Tests."""
    return {
        "category": "general",
        "question": "Was ist StackVertex?",
        "answer": "StackVertex ist eine Multi-Cloud Infrastructure Platform.",
        "sort_order": 0,
        "status": "published",
        "created_by": "admin_user_1",
    }


@pytest.fixture
def sample_category_data():
    """Sample Category data für Tests."""
    return {
        "name": "General",
        "slug": "general",
        "icon": "❓",
        "sort_order": 0,
    }


# =============================================================================
# FAQ Create Tests
# =============================================================================


def test_create_faq(faq_repository, sample_faq_data):
    """Test: FAQ erstellen."""
    faq = faq_repository.create_faq(**sample_faq_data)

    assert faq is not None
    assert "faq_id" in faq
    assert faq["category"] == sample_faq_data["category"]
    assert faq["question"] == sample_faq_data["question"]
    assert faq["answer"] == sample_faq_data["answer"]
    assert faq["sort_order"] == sample_faq_data["sort_order"]
    assert faq["status"] == sample_faq_data["status"]
    assert faq["view_count"] == 0
    assert faq["created_by"] == sample_faq_data["created_by"]
    assert faq["updated_by"] == sample_faq_data["created_by"]
    assert "created_at" in faq
    assert "updated_at" in faq

    # Prüfe DynamoDB Keys
    assert faq["PK"] == f"FAQ#{faq['faq_id']}"
    assert faq["SK"] == "METADATA"
    assert faq["GSI1PK"] == f"faq_category#{sample_faq_data['category']}"
    assert faq["GSI1SK"] == sample_faq_data["sort_order"]
    assert faq["GSI2PK"] == f"faq_status#{sample_faq_data['status']}"


def test_create_faq_defaults(faq_repository):
    """Test: FAQ mit Default-Werten erstellen."""
    faq = faq_repository.create_faq(
        category="technical",
        question="Test Question?",
        answer="Test Answer.",
    )

    assert faq["sort_order"] == 0
    assert faq["status"] == "draft"
    assert faq["view_count"] == 0
    assert faq["created_by"] is None


# =============================================================================
# FAQ Get Tests
# =============================================================================


def test_get_faq(faq_repository, sample_faq_data):
    """Test: FAQ abrufen."""
    created_faq = faq_repository.create_faq(**sample_faq_data)
    faq_id = created_faq["faq_id"]

    retrieved_faq = faq_repository.get_faq(faq_id)

    assert retrieved_faq is not None
    assert retrieved_faq["faq_id"] == faq_id
    assert retrieved_faq["question"] == sample_faq_data["question"]


def test_get_faq_not_found(faq_repository):
    """Test: Nicht existierende FAQ abrufen."""
    faq = faq_repository.get_faq("non-existent-id")
    assert faq is None


# =============================================================================
# FAQ List Tests
# =============================================================================


def test_list_faqs_all(faq_repository, sample_faq_data):
    """Test: Alle FAQs abrufen."""
    # Erstelle mehrere FAQs
    faq_repository.create_faq(**sample_faq_data)
    faq_repository.create_faq(
        category="pricing",
        question="Wie viel kostet StackVertex?",
        answer="Pricing Information",
        sort_order=1,
        status="published",
    )
    faq_repository.create_faq(
        category="general",
        question="Noch eine Frage?",
        answer="Noch eine Antwort",
        sort_order=2,
        status="draft",
    )

    faqs, last_key = faq_repository.list_faqs()

    assert len(faqs) == 3
    assert last_key is None


def test_list_faqs_by_category(faq_repository, sample_faq_data):
    """Test: FAQs nach Kategorie filtern."""
    # Erstelle FAQs in verschiedenen Kategorien
    faq_repository.create_faq(**sample_faq_data)  # general
    faq_repository.create_faq(
        category="general",
        question="Noch eine Frage?",
        answer="Noch eine Antwort",
        sort_order=1,
        status="published",
    )
    faq_repository.create_faq(
        category="pricing",
        question="Pricing Frage?",
        answer="Pricing Antwort",
        sort_order=0,
        status="published",
    )

    # Filter nach general
    faqs, _ = faq_repository.list_faqs(category="general")

    assert len(faqs) == 2
    assert all(faq["category"] == "general" for faq in faqs)


def test_list_faqs_by_status(faq_repository, sample_faq_data):
    """Test: FAQs nach Status filtern."""
    # Erstelle FAQs mit verschiedenen Status
    faq_repository.create_faq(**sample_faq_data)  # published
    faq_repository.create_faq(
        category="general",
        question="Draft Frage?",
        answer="Draft Antwort",
        sort_order=1,
        status="draft",
    )
    faq_repository.create_faq(
        category="pricing",
        question="Noch eine published Frage?",
        answer="Noch eine Antwort",
        sort_order=0,
        status="published",
    )

    # Filter nach published
    faqs, _ = faq_repository.list_faqs(status="published")

    assert len(faqs) == 2
    assert all(faq["status"] == "published" for faq in faqs)


def test_list_faqs_by_category_and_status(faq_repository, sample_faq_data):
    """Test: FAQs nach Kategorie UND Status filtern."""
    # Erstelle FAQs
    faq_repository.create_faq(**sample_faq_data)  # general, published
    faq_repository.create_faq(
        category="general",
        question="Draft Frage?",
        answer="Draft Antwort",
        sort_order=1,
        status="draft",
    )
    faq_repository.create_faq(
        category="pricing",
        question="Pricing published?",
        answer="Pricing Antwort",
        sort_order=0,
        status="published",
    )

    # Filter nach general + published
    faqs, _ = faq_repository.list_faqs(category="general", status="published")

    assert len(faqs) == 1
    assert faqs[0]["category"] == "general"
    assert faqs[0]["status"] == "published"


def test_list_faqs_sorted_by_sort_order(faq_repository):
    """Test: FAQs sortiert nach sort_order."""
    # Erstelle FAQs mit verschiedenen sort_order
    faq_repository.create_faq(
        category="general",
        question="Third FAQ",
        answer="Third",
        sort_order=2,
        status="published",
    )
    faq_repository.create_faq(
        category="general",
        question="First FAQ",
        answer="First",
        sort_order=0,
        status="published",
    )
    faq_repository.create_faq(
        category="general",
        question="Second FAQ",
        answer="Second",
        sort_order=1,
        status="published",
    )

    # Lade FAQs
    faqs, _ = faq_repository.list_faqs(category="general")

    # Prüfe Sortierung (ASC sort_order)
    assert len(faqs) == 3
    assert faqs[0]["sort_order"] == 0
    assert faqs[1]["sort_order"] == 1
    assert faqs[2]["sort_order"] == 2
    assert faqs[0]["question"] == "First FAQ"


# =============================================================================
# FAQ Update Tests
# =============================================================================


def test_update_faq(faq_repository, sample_faq_data):
    """Test: FAQ updaten."""
    created_faq = faq_repository.create_faq(**sample_faq_data)
    faq_id = created_faq["faq_id"]

    # Update
    updated_faq = faq_repository.update_faq(
        faq_id=faq_id,
        updated_by="admin_user_2",
        question="Updated Question?",
        answer="Updated Answer.",
        status="draft",
    )

    assert updated_faq is not None
    assert updated_faq["question"] == "Updated Question?"
    assert updated_faq["answer"] == "Updated Answer."
    assert updated_faq["status"] == "draft"
    assert updated_faq["updated_by"] == "admin_user_2"
    # Prüfe GSI2 Update
    assert updated_faq["GSI2PK"] == "faq_status#draft"


def test_update_faq_category(faq_repository, sample_faq_data):
    """Test: FAQ Kategorie updaten (GSI1 Update)."""
    created_faq = faq_repository.create_faq(**sample_faq_data)
    faq_id = created_faq["faq_id"]

    # Update category
    updated_faq = faq_repository.update_faq(
        faq_id=faq_id,
        updated_by="admin_user_1",
        category="pricing",
    )

    assert updated_faq["category"] == "pricing"
    assert updated_faq["GSI1PK"] == "faq_category#pricing"


def test_update_faq_sort_order(faq_repository, sample_faq_data):
    """Test: FAQ sort_order updaten (GSI1SK Update)."""
    created_faq = faq_repository.create_faq(**sample_faq_data)
    faq_id = created_faq["faq_id"]

    # Update sort_order
    updated_faq = faq_repository.update_faq(
        faq_id=faq_id,
        updated_by="admin_user_1",
        sort_order=99,
    )

    assert updated_faq["sort_order"] == 99
    assert updated_faq["GSI1SK"] == 99


def test_update_faq_not_found(faq_repository):
    """Test: Nicht existierende FAQ updaten."""
    updated_faq = faq_repository.update_faq(
        faq_id="non-existent-id",
        updated_by="admin_user_1",
        question="New Question?",
    )

    assert updated_faq is None


# =============================================================================
# FAQ Delete Tests
# =============================================================================


def test_delete_faq(faq_repository, sample_faq_data):
    """Test: FAQ löschen."""
    created_faq = faq_repository.create_faq(**sample_faq_data)
    faq_id = created_faq["faq_id"]

    # Delete
    success = faq_repository.delete_faq(faq_id)
    assert success is True

    # Verify deleted
    faq = faq_repository.get_faq(faq_id)
    assert faq is None


def test_delete_faq_not_found(faq_repository):
    """Test: Nicht existierende FAQ löschen (idempotent)."""
    # DynamoDB delete_item ist idempotent - gibt immer True zurück
    success = faq_repository.delete_faq("non-existent-id")
    assert success is True


# =============================================================================
# FAQ Reorder Tests
# =============================================================================


def test_reorder_faqs(faq_repository):
    """Test: Sortierung von FAQs ändern."""
    # Erstelle 3 FAQs
    faq1 = faq_repository.create_faq(
        category="general",
        question="FAQ 1",
        answer="Answer 1",
        sort_order=0,
        status="published",
    )
    faq2 = faq_repository.create_faq(
        category="general",
        question="FAQ 2",
        answer="Answer 2",
        sort_order=1,
        status="published",
    )
    faq3 = faq_repository.create_faq(
        category="general",
        question="FAQ 3",
        answer="Answer 3",
        sort_order=2,
        status="published",
    )

    # Neue Reihenfolge: 3, 1, 2
    new_order = [faq3["faq_id"], faq1["faq_id"], faq2["faq_id"]]
    success = faq_repository.reorder_faqs(
        faq_ids_in_order=new_order,
        updated_by="admin_user_1",
    )

    assert success is True

    # Prüfe neue Sortierung
    updated_faq3 = faq_repository.get_faq(faq3["faq_id"])
    updated_faq1 = faq_repository.get_faq(faq1["faq_id"])
    updated_faq2 = faq_repository.get_faq(faq2["faq_id"])

    assert updated_faq3["sort_order"] == 0
    assert updated_faq1["sort_order"] == 1
    assert updated_faq2["sort_order"] == 2


def test_reorder_faqs_with_missing_faq(faq_repository):
    """Test: Reorder mit nicht existierender FAQ (Warning, kein Fehler)."""
    faq1 = faq_repository.create_faq(
        category="general",
        question="FAQ 1",
        answer="Answer 1",
        sort_order=0,
        status="published",
    )

    # Reorder mit nicht existierender FAQ
    new_order = [faq1["faq_id"], "non-existent-id"]
    success = faq_repository.reorder_faqs(
        faq_ids_in_order=new_order,
        updated_by="admin_user_1",
    )

    # Sollte trotzdem True sein (nur Warning geloggt)
    assert success is True


# =============================================================================
# View Count Tests
# =============================================================================


def test_increment_view_count(faq_repository, sample_faq_data):
    """Test: View Count erhöhen."""
    created_faq = faq_repository.create_faq(**sample_faq_data)
    faq_id = created_faq["faq_id"]

    # Initial view_count = 0
    assert created_faq["view_count"] == 0

    # Increment
    updated_faq = faq_repository.increment_view_count(faq_id)

    assert updated_faq is not None
    assert updated_faq["view_count"] == 1

    # Increment again
    updated_faq = faq_repository.increment_view_count(faq_id)
    assert updated_faq["view_count"] == 2


def test_increment_view_count_not_found(faq_repository):
    """Test: View Count für nicht existierende FAQ."""
    updated_faq = faq_repository.increment_view_count("non-existent-id")
    assert updated_faq is None


# =============================================================================
# Category Create Tests
# =============================================================================


def test_create_category(faq_repository, sample_category_data):
    """Test: Kategorie erstellen."""
    category = faq_repository.create_category(**sample_category_data)

    assert category is not None
    assert "category_id" in category
    assert category["name"] == sample_category_data["name"]
    assert category["slug"] == sample_category_data["slug"]
    assert category["icon"] == sample_category_data["icon"]
    assert category["sort_order"] == sample_category_data["sort_order"]
    assert "created_at" in category
    assert "updated_at" in category

    # Prüfe DynamoDB Keys
    assert category["PK"] == f"FAQ_CATEGORY#{category['category_id']}"
    assert category["SK"] == "METADATA"
    assert category["GSI3PK"] == "category_list"
    assert category["GSI3SK"] == sample_category_data["sort_order"]


# =============================================================================
# Category Get Tests
# =============================================================================


def test_get_category(faq_repository, sample_category_data):
    """Test: Kategorie abrufen."""
    created_category = faq_repository.create_category(**sample_category_data)
    category_id = created_category["category_id"]

    retrieved_category = faq_repository.get_category(category_id)

    assert retrieved_category is not None
    assert retrieved_category["category_id"] == category_id
    assert retrieved_category["name"] == sample_category_data["name"]


def test_get_category_not_found(faq_repository):
    """Test: Nicht existierende Kategorie abrufen."""
    category = faq_repository.get_category("non-existent-id")
    assert category is None


# =============================================================================
# Category List Tests
# =============================================================================


def test_list_categories(faq_repository):
    """Test: Kategorien abrufen (sortiert)."""
    # Erstelle Kategorien mit verschiedenen sort_order
    faq_repository.create_category(
        name="Pricing",
        slug="pricing",
        icon="💰",
        sort_order=2,
    )
    faq_repository.create_category(
        name="General",
        slug="general",
        icon="❓",
        sort_order=0,
    )
    faq_repository.create_category(
        name="Technical",
        slug="technical",
        icon="🔧",
        sort_order=1,
    )

    categories = faq_repository.list_categories()

    # Prüfe Sortierung (ASC sort_order)
    assert len(categories) == 3
    assert categories[0]["slug"] == "general"
    assert categories[1]["slug"] == "technical"
    assert categories[2]["slug"] == "pricing"


def test_list_categories_empty(faq_repository):
    """Test: Keine Kategorien vorhanden."""
    categories = faq_repository.list_categories()
    assert len(categories) == 0


# =============================================================================
# Category Update Tests
# =============================================================================


def test_update_category(faq_repository, sample_category_data):
    """Test: Kategorie updaten."""
    created_category = faq_repository.create_category(**sample_category_data)
    category_id = created_category["category_id"]

    # Update
    updated_category = faq_repository.update_category(
        category_id=category_id,
        name="Updated General",
        icon="🆕",
    )

    assert updated_category is not None
    assert updated_category["name"] == "Updated General"
    assert updated_category["icon"] == "🆕"
    assert updated_category["slug"] == sample_category_data["slug"]  # Unchanged


def test_update_category_sort_order(faq_repository, sample_category_data):
    """Test: Kategorie sort_order updaten (GSI3SK Update)."""
    created_category = faq_repository.create_category(**sample_category_data)
    category_id = created_category["category_id"]

    # Update sort_order
    updated_category = faq_repository.update_category(
        category_id=category_id,
        sort_order=99,
    )

    assert updated_category["sort_order"] == 99
    assert updated_category["GSI3SK"] == 99


def test_update_category_not_found(faq_repository):
    """Test: Nicht existierende Kategorie updaten."""
    updated_category = faq_repository.update_category(
        category_id="non-existent-id",
        name="New Name",
    )

    assert updated_category is None


# =============================================================================
# Category Delete Tests
# =============================================================================


def test_delete_category(faq_repository, sample_category_data):
    """Test: Kategorie löschen."""
    created_category = faq_repository.create_category(**sample_category_data)
    category_id = created_category["category_id"]

    # Delete
    success = faq_repository.delete_category(category_id)
    assert success is True

    # Verify deleted
    category = faq_repository.get_category(category_id)
    assert category is None


def test_delete_category_not_found(faq_repository):
    """Test: Nicht existierende Kategorie löschen (idempotent)."""
    # DynamoDB delete_item ist idempotent - gibt immer True zurück
    success = faq_repository.delete_category("non-existent-id")
    assert success is True


# =============================================================================
# Analytics Tests
# =============================================================================


def test_get_top_viewed_faqs(faq_repository):
    """Test: Top viewed FAQs abrufen."""
    # Erstelle FAQs mit verschiedenen view_counts
    faq1 = faq_repository.create_faq(
        category="general",
        question="FAQ 1",
        answer="Answer 1",
        status="published",
    )
    faq2 = faq_repository.create_faq(
        category="general",
        question="FAQ 2",
        answer="Answer 2",
        status="published",
    )
    faq3 = faq_repository.create_faq(
        category="general",
        question="FAQ 3",
        answer="Answer 3",
        status="published",
    )

    # Setze view_counts
    for _ in range(5):
        faq_repository.increment_view_count(faq1["faq_id"])
    for _ in range(10):
        faq_repository.increment_view_count(faq2["faq_id"])
    for _ in range(2):
        faq_repository.increment_view_count(faq3["faq_id"])

    # Lade top viewed
    top_faqs = faq_repository.get_top_viewed_faqs(limit=2)

    # Prüfe Sortierung (DESC view_count)
    assert len(top_faqs) == 2
    assert top_faqs[0]["faq_id"] == faq2["faq_id"]
    assert top_faqs[0]["view_count"] == 10
    assert top_faqs[1]["faq_id"] == faq1["faq_id"]
    assert top_faqs[1]["view_count"] == 5


def test_get_unviewed_faqs(faq_repository):
    """Test: FAQs ohne Views abrufen."""
    # Erstelle FAQs
    faq1 = faq_repository.create_faq(
        category="general",
        question="FAQ 1",
        answer="Answer 1",
        status="published",
    )
    faq2 = faq_repository.create_faq(
        category="general",
        question="FAQ 2",
        answer="Answer 2",
        status="published",
    )
    faq3 = faq_repository.create_faq(
        category="general",
        question="FAQ 3",
        answer="Answer 3",
        status="published",
    )

    # Nur faq2 Views geben
    faq_repository.increment_view_count(faq2["faq_id"])

    # Lade unviewed FAQs
    unviewed = faq_repository.get_unviewed_faqs()

    # Nur faq1 und faq3 sollten view_count = 0 haben
    assert len(unviewed) == 2
    unviewed_ids = {faq["faq_id"] for faq in unviewed}
    assert faq1["faq_id"] in unviewed_ids
    assert faq3["faq_id"] in unviewed_ids
    assert faq2["faq_id"] not in unviewed_ids
