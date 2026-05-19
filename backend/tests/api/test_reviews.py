"""API Tests für Review Endpoints.

Tests für:
- Public Endpoints (submit, list, stats)
- Rate Limiting
- Admin Endpoints (list, approve, reject, spam, bulk-approve, delete)
- Authentication & Authorization
"""

import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock

from app.repositories.review import ReviewRepository


class TestPublicReviewEndpoints:
    """Tests für Public Review Endpoints (ohne Auth)."""

    def test_submit_review_success(self, client, mock_dynamodb_table):
        """Test POST /reviews (success)."""
        response = client.post(
            "/api/v1/reviews",
            json={
                "name": "Max Mustermann",
                "email": "max@example.com",
                "rating": 5,
                "comment": "Sehr gutes Produkt! Bin sehr zufrieden damit."
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == "Max Mustermann"
        assert data["rating"] == 5
        assert data["comment"] == "Sehr gutes Produkt! Bin sehr zufrieden damit."
        assert "id" in data
        assert "created_at" in data

        # Email sollte NICHT in response sein (privat)
        assert "email" not in data
        assert "ip_address" not in data

    def test_submit_review_invalid_rating(self, client, mock_dynamodb_table):
        """Test POST /reviews mit ungültigem Rating."""
        response = client.post(
            "/api/v1/reviews",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "rating": 6,  # Ungültig (> 5)
                "comment": "This review has invalid rating."
            }
        )

        assert response.status_code == 422  # Pydantic validation
        # Pydantic liefert englische Fehlermeldungen
        data = response.json()
        assert "detail" in data
        assert data["detail"][0]["loc"] == ["body", "rating"]

    def test_submit_review_comment_too_short(self, client, mock_dynamodb_table):
        """Test POST /reviews mit zu kurzem Kommentar."""
        response = client.post(
            "/api/v1/reviews",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "rating": 5,
                "comment": "Short"  # Zu kurz
            }
        )

        assert response.status_code == 422  # Pydantic validation
        data = response.json()
        assert "detail" in data
        assert data["detail"][0]["loc"] == ["body", "comment"]
        assert data["detail"][0]["type"] == "string_too_short"

    def test_submit_review_comment_too_long(self, client, mock_dynamodb_table):
        """Test POST /reviews mit zu langem Kommentar."""
        long_comment = "x" * 501  # > 500 Zeichen

        response = client.post(
            "/api/v1/reviews",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "rating": 5,
                "comment": long_comment
            }
        )

        assert response.status_code == 422  # Pydantic validation
        data = response.json()
        assert "detail" in data
        assert data["detail"][0]["loc"] == ["body", "comment"]
        assert data["detail"][0]["type"] == "string_too_long"

    def test_submit_review_invalid_email(self, client, mock_dynamodb_table):
        """Test POST /reviews mit ungültiger Email (Pydantic Validation)."""
        response = client.post(
            "/api/v1/reviews",
            json={
                "name": "Test User",
                "email": "invalid-email",  # Ungültige Email
                "rating": 5,
                "comment": "This review has invalid email format."
            }
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_submit_review_missing_fields(self, client, mock_dynamodb_table):
        """Test POST /reviews mit fehlenden Pflichtfeldern."""
        response = client.post(
            "/api/v1/reviews",
            json={
                "name": "Test User"
                # Email, Rating, Comment fehlen
            }
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_submit_review_rate_limit(self, client, mock_dynamodb_table):
        """Test Rate Limiting (3 reviews/hour per IP)."""
        # Rate limiting requires real limiter setup mit Redis
        # Dieser Test würde komplexes Setup mit fakeredis benötigen
        pytest.skip("Rate limiting testing requires real Redis setup")

    def test_get_public_reviews_empty(self, client, mock_dynamodb_table):
        """Test GET /reviews (keine approved reviews)."""
        response = client.get("/api/v1/reviews")

        assert response.status_code == 200
        data = response.json()

        assert data["reviews"] == []
        assert data["stats"]["count"] == 0
        assert data["stats"]["average"] == 0.0

    def test_get_public_reviews_only_approved(self, client, mock_dynamodb_table):
        """Test GET /reviews (nur approved reviews sichtbar)."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create reviews (pending)
        review1 = repo.create(
            "User1", "user1@example.com", 5, "Approved review for public display test."
        )
        review2 = repo.create(
            "User2", "user2@example.com", 4, "Pending review should not appear."
        )

        # Approve nur Review 1
        repo.update_status(review1["id"], "approved", "admin123")

        # Get public reviews
        response = client.get("/api/v1/reviews")

        assert response.status_code == 200
        data = response.json()

        assert len(data["reviews"]) == 1
        assert data["reviews"][0]["id"] == review1["id"]
        assert data["reviews"][0]["rating"] == 5

    def test_get_public_reviews_no_private_fields(self, client, mock_dynamodb_table):
        """Test GET /reviews (keine privaten Felder)."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create and approve review
        review = repo.create(
            name="Public User",
            email="public@example.com",
            rating=5,
            comment="This review should be public without private data.",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        repo.update_status(review["id"], "approved", "admin123")

        # Get public reviews
        response = client.get("/api/v1/reviews")

        assert response.status_code == 200
        data = response.json()

        public_review = data["reviews"][0]

        # Public fields
        assert "id" in public_review
        assert "name" in public_review
        assert "rating" in public_review
        assert "comment" in public_review
        assert "created_at" in public_review

        # Private fields sollten NICHT existieren
        assert "email" not in public_review
        assert "ip_address" not in public_review
        assert "user_agent" not in public_review
        assert "status" not in public_review

    def test_get_public_reviews_with_limit(self, client, mock_dynamodb_table):
        """Test GET /reviews?limit=5."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create and approve many reviews
        for i in range(10):
            review = repo.create(
                f"User{i}",
                f"user{i}@example.com",
                5,
                f"Review number {i} for testing limit functionality."
            )
            repo.update_status(review["id"], "approved", "admin123")

        # Get only 5 reviews
        response = client.get("/api/v1/reviews?limit=5")

        assert response.status_code == 200
        data = response.json()

        assert len(data["reviews"]) == 5

    def test_get_rating_stats_empty(self, client, mock_dynamodb_table):
        """Test GET /reviews/stats (keine Reviews)."""
        response = client.get("/api/v1/reviews/stats")

        assert response.status_code == 200
        data = response.json()

        assert data["average"] == 0.0
        assert data["count"] == 0
        assert data["distribution"] == {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

    def test_get_rating_stats_with_reviews(self, client, mock_dynamodb_table):
        """Test GET /reviews/stats mit Reviews."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create and approve reviews
        reviews = [
            repo.create("User1", "user1@example.com", 5, "Perfect product, excellent quality!"),
            repo.create("User2", "user2@example.com", 4, "Very good product, highly recommend."),
            repo.create("User3", "user3@example.com", 5, "Amazing product, best purchase!"),
        ]

        for review in reviews:
            repo.update_status(review["id"], "approved", "admin123")

        # Get stats
        response = client.get("/api/v1/reviews/stats")

        assert response.status_code == 200
        data = response.json()

        assert data["count"] == 3
        assert data["average"] == pytest.approx(4.67, rel=0.01)
        assert int(data["distribution"]["5"]) == 2
        assert int(data["distribution"]["4"]) == 1


class TestAdminReviewEndpoints:
    """Tests für Admin Review Endpoints (mit Auth)."""

    def test_list_all_reviews_unauthorized(self, client, mock_dynamodb_table):
        """Test GET /admin/reviews ohne Auth (401)."""
        response = client.get("/api/v1/admin/reviews")

        assert response.status_code == 401

    def test_list_all_reviews_admin(self, authenticated_client, mock_dynamodb_table):
        """Test GET /admin/reviews mit Auth."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create reviews
        repo.create("User1", "user1@example.com", 5, "Pending review for admin list test.")
        repo.create("User2", "user2@example.com", 4, "Another pending review for admin.")

        response = authenticated_client.get("/api/v1/admin/reviews")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        # Admin sieht alle Felder (inkl. email, IP, etc.)
        assert "email" in data[0]

    def test_list_all_reviews_filtered_by_status(self, authenticated_client, mock_dynamodb_table):
        """Test GET /admin/reviews?status=pending."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create reviews
        review1 = repo.create("User1", "user1@example.com", 5, "Pending review number one.")
        review2 = repo.create("User2", "user2@example.com", 4, "Pending review number two.")

        repo.update_status(review2["id"], "approved", "admin123")

        response = authenticated_client.get("/api/v1/admin/reviews?status_filter=pending")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["id"] == review1["id"]

    def test_approve_review_unauthorized(self, client, mock_dynamodb_table):
        """Test PATCH /admin/reviews/{id}/approve ohne Auth (401)."""
        fake_id = str(uuid4())
        response = client.patch(f"/api/v1/admin/reviews/{fake_id}/approve")

        assert response.status_code == 401

    def test_approve_review_admin(self, authenticated_client, mock_dynamodb_table, mock_superadmin_user):
        """Test PATCH /admin/reviews/{id}/approve mit Auth."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create review
        review = repo.create(
            "Test User",
            "test@example.com",
            5,
            "This review will be approved for testing."
        )

        response = authenticated_client.patch(f"/api/v1/admin/reviews/{review['id']}/approve")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "approved"
        assert data["approved_by"] == mock_superadmin_user["id"]
        assert "approved_at" in data

    def test_approve_review_not_found(self, authenticated_client, mock_dynamodb_table):
        """Test PATCH /admin/reviews/{id}/approve (Review nicht gefunden)."""
        fake_id = str(uuid4())
        response = authenticated_client.patch(f"/api/v1/admin/reviews/{fake_id}/approve")

        assert response.status_code == 404

    def test_reject_review_unauthorized(self, client, mock_dynamodb_table):
        """Test PATCH /admin/reviews/{id}/reject ohne Auth (401)."""
        fake_id = str(uuid4())
        response = client.patch(
            f"/api/v1/admin/reviews/{fake_id}/reject",
            json={"status": "rejected", "reason": "Nicht relevant"}
        )

        assert response.status_code == 401

    def test_reject_review_admin(self, authenticated_client, mock_dynamodb_table, mock_superadmin_user):
        """Test PATCH /admin/reviews/{id}/reject mit Auth."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create review
        review = repo.create(
            "Test User",
            "test@example.com",
            2,
            "This review will be rejected for testing."
        )

        response = authenticated_client.patch(
            f"/api/v1/admin/reviews/{review['id']}/reject",
            json={"status": "rejected", "reason": "Nicht relevant"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "rejected"
        assert data["rejected_by"] == mock_superadmin_user["id"]
        assert data["rejected_reason"] == "Nicht relevant"
        assert "rejected_at" in data

    def test_reject_review_not_found(self, authenticated_client, mock_dynamodb_table):
        """Test PATCH /admin/reviews/{id}/reject (Review nicht gefunden)."""
        fake_id = str(uuid4())
        response = authenticated_client.patch(
            f"/api/v1/admin/reviews/{fake_id}/reject",
            json={"status": "rejected"}
        )

        assert response.status_code == 404

    def test_mark_spam_unauthorized(self, client, mock_dynamodb_table):
        """Test PATCH /admin/reviews/{id}/spam ohne Auth (401)."""
        fake_id = str(uuid4())
        response = client.patch(f"/api/v1/admin/reviews/{fake_id}/spam")

        assert response.status_code == 401

    def test_mark_spam_admin(self, authenticated_client, mock_dynamodb_table):
        """Test PATCH /admin/reviews/{id}/spam mit Auth."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create review
        review = repo.create(
            "Test User",
            "test@example.com",
            5,
            "This is a normal review that admin marks as spam."
        )

        response = authenticated_client.patch(f"/api/v1/admin/reviews/{review['id']}/spam")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "spam"

    def test_mark_spam_not_found(self, authenticated_client, mock_dynamodb_table):
        """Test PATCH /admin/reviews/{id}/spam (Review nicht gefunden)."""
        fake_id = str(uuid4())
        response = authenticated_client.patch(f"/api/v1/admin/reviews/{fake_id}/spam")

        assert response.status_code == 404

    def test_bulk_approve_unauthorized(self, client, mock_dynamodb_table):
        """Test POST /admin/reviews/bulk-approve ohne Auth (401)."""
        response = client.post(
            "/api/v1/admin/reviews/bulk-approve",
            json={"review_ids": [str(uuid4())], "action": "approve"}
        )

        assert response.status_code == 401

    def test_bulk_approve_admin(self, authenticated_client, mock_dynamodb_table):
        """Test POST /admin/reviews/bulk-approve mit Auth."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create multiple reviews
        reviews = [
            repo.create("User1", "user1@example.com", 5, "Review one for bulk approval test."),
            repo.create("User2", "user2@example.com", 4, "Review two for bulk approval test."),
            repo.create("User3", "user3@example.com", 5, "Review three for bulk approval test."),
        ]

        review_ids = [r["id"] for r in reviews]

        response = authenticated_client.post(
            "/api/v1/admin/reviews/bulk-approve",
            json={"review_ids": review_ids, "action": "approve"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success_count"] == 3
        assert data["failed_count"] == 0
        assert data["total"] == 3

    def test_bulk_approve_partial_failure(self, authenticated_client, mock_dynamodb_table):
        """Test POST /admin/reviews/bulk-approve (teilweise Fehler)."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create one review
        review = repo.create(
            "Existing User",
            "existing@example.com",
            5,
            "This review exists for partial bulk test."
        )

        # Non-existent review
        fake_id = str(uuid4())

        response = authenticated_client.post(
            "/api/v1/admin/reviews/bulk-approve",
            json={"review_ids": [review["id"], fake_id], "action": "approve"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success_count"] == 1
        assert data["failed_count"] == 1
        assert data["total"] == 2

    def test_delete_review_unauthorized(self, client, mock_dynamodb_table):
        """Test DELETE /admin/reviews/{id} ohne Auth (401)."""
        fake_id = str(uuid4())
        response = client.delete(f"/api/v1/admin/reviews/{fake_id}")

        assert response.status_code == 401

    def test_delete_review_admin(self, authenticated_client, mock_dynamodb_table):
        """Test DELETE /admin/reviews/{id} mit Auth."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create review
        review = repo.create(
            "Delete User",
            "delete@example.com",
            3,
            "This review will be deleted for testing."
        )

        response = authenticated_client.delete(f"/api/v1/admin/reviews/{review['id']}")

        assert response.status_code == 204  # No Content

        # Verify deletion
        assert repo.get(review["id"]) is None

    def test_delete_review_not_found(self, authenticated_client, mock_dynamodb_table):
        """Test DELETE /admin/reviews/{id} (Review nicht gefunden).

        Note: DELETE is idempotent - returns 204 even if review doesn't exist.
        """
        fake_id = str(uuid4())
        response = authenticated_client.delete(f"/api/v1/admin/reviews/{fake_id}")

        assert response.status_code == 204  # Idempotent delete


class TestReviewAPIValidation:
    """Tests für API Validation (Pydantic Schemas)."""

    def test_submit_review_pydantic_validation_name_too_short(self, client, mock_dynamodb_table):
        """Test Name Validation (min_length=2)."""
        response = client.post(
            "/api/v1/reviews",
            json={
                "name": "A",  # Nur 1 Zeichen
                "email": "test@example.com",
                "rating": 5,
                "comment": "This review has name too short."
            }
        )

        assert response.status_code == 422

    def test_submit_review_pydantic_validation_name_too_long(self, client, mock_dynamodb_table):
        """Test Name Validation (max_length=100)."""
        long_name = "A" * 101  # > 100 Zeichen

        response = client.post(
            "/api/v1/reviews",
            json={
                "name": long_name,
                "email": "test@example.com",
                "rating": 5,
                "comment": "This review has name too long."
            }
        )

        assert response.status_code == 422

    def test_submit_review_pydantic_validation_comment_stripped(self, client, mock_dynamodb_table):
        """Test dass Comment Whitespace getrimmt wird."""
        response = client.post(
            "/api/v1/reviews",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "rating": 5,
                "comment": "   This comment has leading/trailing spaces.   "
            }
        )

        assert response.status_code == 201
        data = response.json()

        # Whitespace sollte getrimmt sein
        assert data["comment"] == "This comment has leading/trailing spaces."
