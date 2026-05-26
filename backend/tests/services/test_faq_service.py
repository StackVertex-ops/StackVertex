"""Tests für FAQ Service.

Testet Business Logic für FAQ Management:
- Public FAQ Access (nur published)
- FAQ Search (case-insensitive)
- Admin FAQ Management
- Category Management
- Analytics
- View Tracking
"""

import pytest
from datetime import datetime


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def faq_repository(mock_dynamodb_table):
    """Provide FaqRepository with mocked DynamoDB table."""
    from app.repositories.faq import FaqRepository

    return FaqRepository(table=mock_dynamodb_table)


@pytest.fixture
def faq_service(faq_repository):
    """Provide FaqService with FaqRepository."""
    from app.services.faq_service import FaqService

    return FaqService(faq_repo=faq_repository)


@pytest.fixture
def setup_categories(faq_repository):
    """Setup standard categories für Tests."""
    categories = [
        {"name": "General", "slug": "general", "icon": "❓", "sort_order": 0},
        {"name": "Pricing", "slug": "pricing", "icon": "💰", "sort_order": 1},
        {"name": "Technical", "slug": "technical", "icon": "🔧", "sort_order": 2},
    ]

    for cat_data in categories:
        faq_repository.create_category(**cat_data)

    return categories


@pytest.fixture
def setup_faqs(faq_repository, setup_categories):
    """Setup sample FAQs für Tests."""
    faqs = [
        # Published FAQs
        {
            "category": "general",
            "question": "Was ist StackVertex?",
            "answer": "StackVertex ist eine Multi-Cloud Platform.",
            "sort_order": 0,
            "status": "published",
        },
        {
            "category": "general",
            "question": "Wie funktioniert StackVertex?",
            "answer": "StackVertex verwendet JSON-basierte Architektur-Definitionen.",
            "sort_order": 1,
            "status": "published",
        },
        {
            "category": "pricing",
            "question": "Wie viel kostet StackVertex?",
            "answer": "Pricing starts at $10/month. Contact us for details.",
            "sort_order": 0,
            "status": "published",
        },
        {
            "category": "technical",
            "question": "Welche Cloud-Provider werden unterstützt?",
            "answer": "AWS, Azure, und GCP werden unterstützt.",
            "sort_order": 0,
            "status": "published",
        },
        # Draft FAQs
        {
            "category": "general",
            "question": "Draft FAQ?",
            "answer": "This is a draft FAQ.",
            "sort_order": 2,
            "status": "draft",
        },
    ]

    created_faqs = []
    for faq_data in faqs:
        created_faq = faq_repository.create_faq(**faq_data)
        created_faqs.append(created_faq)

    return created_faqs


# =============================================================================
# Public FAQ Access Tests
# =============================================================================


def test_get_public_faqs_all(faq_service, setup_faqs):
    """Test: Alle published FAQs abrufen (gruppiert nach Kategorie)."""
    result = faq_service.get_public_faqs()

    assert "categories" in result
    assert "total" in result
    assert result["total"] == 4  # Nur published FAQs

    # Prüfe Kategorien-Struktur
    categories = result["categories"]
    assert len(categories) == 3  # general, pricing, technical

    # Finde General-Kategorie
    general_cat = next(cat for cat in categories if cat["slug"] == "general")
    assert len(general_cat["faqs"]) == 2  # Nur published
    assert general_cat["name"] == "General"
    assert general_cat["icon"] == "❓"


def test_get_public_faqs_by_category(faq_service, setup_faqs):
    """Test: Published FAQs nach Kategorie filtern."""
    result = faq_service.get_public_faqs(category="pricing")

    assert "category" in result
    assert result["category"] == "pricing"
    assert "faqs" in result
    assert len(result["faqs"]) == 1
    assert result["total"] == 1
    assert result["faqs"][0]["question"] == "Wie viel kostet StackVertex?"


def test_get_public_faqs_excludes_drafts(faq_service, setup_faqs):
    """Test: Draft FAQs werden nicht zurückgegeben."""
    result = faq_service.get_public_faqs(category="general")

    # Prüfe dass Draft nicht enthalten ist
    questions = [faq["question"] for faq in result["faqs"]]
    assert "Draft FAQ?" not in questions


# =============================================================================
# FAQ Search Tests
# =============================================================================


def test_search_faqs_by_question(faq_service, setup_faqs):
    """Test: Suche in FAQ-Frage."""
    results = faq_service.search_faqs(query="StackVertex")

    # Sollte mindestens 2 FAQs finden (beide mit "StackVertex" in der Frage)
    assert len(results) >= 2
    questions = [faq["question"] for faq in results]
    assert "Was ist StackVertex?" in questions
    assert "Wie viel kostet StackVertex?" in questions


def test_search_faqs_by_answer(faq_service, setup_faqs):
    """Test: Suche in FAQ-Antwort."""
    results = faq_service.search_faqs(query="JSON")

    # Sollte FAQ finden, die "JSON" in der Antwort hat
    assert len(results) >= 1
    assert any("JSON" in faq["answer"] for faq in results)


def test_search_faqs_case_insensitive(faq_service, setup_faqs):
    """Test: Suche ist case-insensitive."""
    # Suche mit verschiedenen Cases
    results_lower = faq_service.search_faqs(query="stackvertex")
    results_upper = faq_service.search_faqs(query="OVERCLOUD")
    results_mixed = faq_service.search_faqs(query="StackVertex")

    # Sollten alle gleich viele Ergebnisse liefern
    assert len(results_lower) == len(results_upper)
    assert len(results_upper) == len(results_mixed)
    assert len(results_lower) >= 2


def test_search_faqs_excludes_drafts(faq_service, setup_faqs):
    """Test: Draft FAQs werden nicht durchsucht."""
    results = faq_service.search_faqs(query="draft")

    # Sollte keine Ergebnisse finden (draft FAQ ist draft)
    assert len(results) == 0


def test_search_faqs_no_results(faq_service, setup_faqs):
    """Test: Suche ohne Ergebnisse."""
    results = faq_service.search_faqs(query="xyz123notfound")

    assert len(results) == 0


# =============================================================================
# FAQ Detail Tests
# =============================================================================


def test_get_faq_detail_with_tracking(faq_service, faq_repository, setup_faqs):
    """Test: Einzelnes FAQ abrufen mit View-Tracking."""
    faq = setup_faqs[0]
    faq_id = faq["faq_id"]

    # Initial view_count = 0
    initial_faq = faq_repository.get_faq(faq_id)
    assert initial_faq["view_count"] == 0

    # Get detail (mit tracking)
    result = faq_service.get_faq_detail(faq_id=faq_id, track_view=True)

    assert result is not None
    assert result["faq_id"] == faq_id
    assert result["view_count"] == 1  # Erhöht

    # Nochmal abrufen
    result = faq_service.get_faq_detail(faq_id=faq_id, track_view=True)
    assert result["view_count"] == 2


def test_get_faq_detail_without_tracking(faq_service, faq_repository, setup_faqs):
    """Test: FAQ abrufen ohne View-Tracking."""
    faq = setup_faqs[0]
    faq_id = faq["faq_id"]

    # Get detail (ohne tracking)
    result = faq_service.get_faq_detail(faq_id=faq_id, track_view=False)

    assert result is not None
    assert result["view_count"] == 0  # Nicht erhöht


def test_get_faq_detail_not_found(faq_service):
    """Test: Nicht existierendes FAQ abrufen."""
    result = faq_service.get_faq_detail(faq_id="non-existent-id")
    assert result is None


def test_get_faq_detail_draft_not_public(faq_service, setup_faqs):
    """Test: Draft FAQ nicht öffentlich zugänglich."""
    draft_faq = next(faq for faq in setup_faqs if faq["status"] == "draft")
    faq_id = draft_faq["faq_id"]

    # Get detail sollte None zurückgeben (nur published öffentlich)
    result = faq_service.get_faq_detail(faq_id=faq_id, track_view=True)
    assert result is None


# =============================================================================
# Admin FAQ Management Tests
# =============================================================================


def test_list_all_faqs_admin(faq_service, setup_faqs):
    """Test: Admin kann alle FAQs sehen (inkl. drafts)."""
    faqs = faq_service.list_all_faqs()

    # Sollte ALLE FAQs enthalten (5 insgesamt)
    assert len(faqs) == 5

    # Prüfe dass drafts enthalten sind
    statuses = [faq["status"] for faq in faqs]
    assert "draft" in statuses
    assert "published" in statuses


def test_list_all_faqs_admin_filter_status(faq_service, setup_faqs):
    """Test: Admin filtert nach Status."""
    published = faq_service.list_all_faqs(status="published")
    drafts = faq_service.list_all_faqs(status="draft")

    assert len(published) == 4
    assert len(drafts) == 1


def test_list_all_faqs_admin_filter_category(faq_service, setup_faqs):
    """Test: Admin filtert nach Kategorie."""
    general_faqs = faq_service.list_all_faqs(category="general")

    # Sollte 3 FAQs enthalten (2 published + 1 draft)
    assert len(general_faqs) == 3


def test_create_faq_admin(faq_service, faq_repository):
    """Test: Admin erstellt FAQ."""
    faq = faq_service.create_faq(
        admin_id="admin_user_1",
        category="security",
        question="Ist StackVertex sicher?",
        answer="Ja, mit End-to-End-Verschlüsselung.",
        status="published",
        sort_order=0,
    )

    assert faq is not None
    assert faq["question"] == "Ist StackVertex sicher?"
    assert faq["status"] == "published"
    assert faq["created_by"] == "admin_user_1"


def test_update_faq_admin(faq_service, setup_faqs):
    """Test: Admin updated FAQ."""
    faq = setup_faqs[0]
    faq_id = faq["faq_id"]

    updated_faq = faq_service.update_faq(
        faq_id=faq_id,
        admin_id="admin_user_2",
        question="Updated Question?",
        status="draft",
    )

    assert updated_faq is not None
    assert updated_faq["question"] == "Updated Question?"
    assert updated_faq["status"] == "draft"
    assert updated_faq["updated_by"] == "admin_user_2"


def test_delete_faq_admin(faq_service, faq_repository, setup_faqs):
    """Test: Admin löscht FAQ."""
    faq = setup_faqs[0]
    faq_id = faq["faq_id"]

    success = faq_service.delete_faq(faq_id=faq_id)
    assert success is True

    # Prüfe dass FAQ gelöscht ist
    deleted_faq = faq_repository.get_faq(faq_id)
    assert deleted_faq is None


def test_reorder_faqs_admin(faq_service, faq_repository, setup_faqs):
    """Test: Admin ändert Sortierung."""
    # Nehme erste 3 FAQs
    faq1 = setup_faqs[0]
    faq2 = setup_faqs[1]
    faq3 = setup_faqs[2]

    # Neue Reihenfolge: 3, 1, 2
    new_order = [faq3["faq_id"], faq1["faq_id"], faq2["faq_id"]]
    success = faq_service.reorder_faqs(
        faq_ids=new_order,
        admin_id="admin_user_1",
    )

    assert success is True

    # Prüfe neue sort_order
    updated_faq3 = faq_repository.get_faq(faq3["faq_id"])
    updated_faq1 = faq_repository.get_faq(faq1["faq_id"])
    updated_faq2 = faq_repository.get_faq(faq2["faq_id"])

    assert updated_faq3["sort_order"] == 0
    assert updated_faq1["sort_order"] == 1
    assert updated_faq2["sort_order"] == 2


# =============================================================================
# Category Management Tests
# =============================================================================


def test_get_categories(faq_service, setup_categories):
    """Test: Kategorien abrufen."""
    categories = faq_service.get_categories()

    assert len(categories) == 3
    assert categories[0]["slug"] == "general"
    assert categories[1]["slug"] == "pricing"
    assert categories[2]["slug"] == "technical"


def test_create_category_admin(faq_service, faq_repository):
    """Test: Admin erstellt Kategorie."""
    category = faq_service.create_category(
        name="Security",
        slug="security",
        icon="🔒",
        sort_order=99,
    )

    assert category is not None
    assert category["name"] == "Security"
    assert category["slug"] == "security"
    assert category["icon"] == "🔒"
    assert category["sort_order"] == 99


def test_update_category_admin(faq_service, setup_categories, faq_repository):
    """Test: Admin updated Kategorie."""
    # Hole erste Kategorie
    categories = faq_repository.list_categories()
    category_id = categories[0]["category_id"]

    updated_category = faq_service.update_category(
        category_id=category_id,
        name="Updated General",
        icon="🆕",
    )

    assert updated_category is not None
    assert updated_category["name"] == "Updated General"
    assert updated_category["icon"] == "🆕"


def test_delete_category_admin(faq_service, faq_repository, setup_categories):
    """Test: Admin löscht Kategorie."""
    # Hole erste Kategorie
    categories = faq_repository.list_categories()
    category_id = categories[0]["category_id"]

    success = faq_service.delete_category(category_id=category_id)
    assert success is True

    # Prüfe dass Kategorie gelöscht ist
    deleted_category = faq_repository.get_category(category_id)
    assert deleted_category is None


# =============================================================================
# Analytics Tests
# =============================================================================


def test_get_faq_analytics(faq_service, faq_repository, setup_faqs):
    """Test: FAQ Analytics abrufen."""
    # Setze view_counts
    faq_repository.increment_view_count(setup_faqs[0]["faq_id"])
    faq_repository.increment_view_count(setup_faqs[0]["faq_id"])
    faq_repository.increment_view_count(setup_faqs[1]["faq_id"])
    faq_repository.increment_view_count(setup_faqs[1]["faq_id"])
    faq_repository.increment_view_count(setup_faqs[1]["faq_id"])
    faq_repository.increment_view_count(setup_faqs[2]["faq_id"])

    analytics = faq_service.get_faq_analytics()

    assert "total_faqs" in analytics
    assert "published" in analytics
    assert "drafts" in analytics
    assert "total_views" in analytics
    assert "top_viewed" in analytics
    assert "unviewed_count" in analytics

    assert analytics["total_faqs"] == 5
    assert analytics["published"] == 4
    assert analytics["drafts"] == 1
    assert analytics["total_views"] == 6  # 2 + 3 + 1

    # Top viewed sollte richtig sortiert sein
    top_viewed = analytics["top_viewed"]
    assert len(top_viewed) >= 2
    assert top_viewed[0]["view_count"] == 3  # setup_faqs[1]
    assert top_viewed[1]["view_count"] == 2  # setup_faqs[0]


def test_get_faq_analytics_unviewed(faq_service, faq_repository, setup_faqs):
    """Test: Unviewed FAQs in Analytics."""
    # Nur eine FAQ Views geben
    faq_repository.increment_view_count(setup_faqs[0]["faq_id"])

    analytics = faq_service.get_faq_analytics()

    # 3 published FAQs sollten unviewed sein
    assert analytics["unviewed_count"] == 3


def test_get_faq_analytics_empty(faq_service):
    """Test: Analytics ohne FAQs."""
    analytics = faq_service.get_faq_analytics()

    assert analytics["total_faqs"] == 0
    assert analytics["published"] == 0
    assert analytics["drafts"] == 0
    assert analytics["total_views"] == 0
    assert len(analytics["top_viewed"]) == 0
    assert analytics["unviewed_count"] == 0
