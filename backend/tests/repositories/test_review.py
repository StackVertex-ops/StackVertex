"""Unit Tests für ReviewRepository.

Tests für:
- Review Creation (mit Spam Detection)
- Review Retrieval (get, list_by_status, list_by_rating)
- Review Updates (status changes)
- Bulk Operations
- Rating Statistics
- Spam Detection Logic
"""

import pytest
from uuid import uuid4

from app.repositories.review import ReviewRepository


class TestReviewRepository:
    """Tests für ReviewRepository."""

    def test_create_review_pending(self, mock_dynamodb_table):
        """Test Review Creation (status: pending)."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        review = repo.create(
            name="Max Mustermann",
            email="max@example.com",
            rating=5,
            comment="Sehr gutes Produkt! Bin sehr zufrieden."
        )

        assert review["name"] == "Max Mustermann"
        assert review["email"] == "max@example.com"
        assert review["rating"] == 5
        assert review["comment"] == "Sehr gutes Produkt! Bin sehr zufrieden."
        assert review["status"] == "pending"
        assert review["is_spam"] is False
        assert "id" in review
        assert "created_at" in review
        assert review["GSI1PK"] == "review_status#pending"
        assert review["GSI2PK"] == "review_rating#5"

    def test_create_review_with_metadata(self, mock_dynamodb_table):
        """Test Review Creation mit IP und User-Agent."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        review = repo.create(
            name="Anna Schmidt",
            email="anna@example.com",
            rating=4,
            comment="Gutes Produkt, kleine Verbesserungen möglich.",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )

        assert review["ip_address"] == "192.168.1.1"
        assert review["user_agent"] == "Mozilla/5.0"

    def test_create_review_email_lowercase(self, mock_dynamodb_table):
        """Test dass Email automatisch lowercase wird."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        review = repo.create(
            name="Test User",
            email="TEST@EXAMPLE.COM",
            rating=3,
            comment="Test comment for email lowercase"
        )

        assert review["email"] == "test@example.com"

    def test_get_review(self, mock_dynamodb_table):
        """Test Review Retrieval."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create review
        created = repo.create(
            name="Test User",
            email="test@example.com",
            rating=5,
            comment="Test review for retrieval"
        )

        review_id = created["id"]

        # Get review
        retrieved = repo.get(review_id)

        assert retrieved is not None
        assert retrieved["id"] == review_id
        assert retrieved["name"] == "Test User"
        assert retrieved["rating"] == 5

    def test_get_review_not_found(self, mock_dynamodb_table):
        """Test Get Non-Existent Review."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        result = repo.get(uuid4())

        assert result is None

    def test_list_by_status_pending(self, mock_dynamodb_table):
        """Test List Reviews by Status (pending)."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create multiple reviews
        repo.create(
            name="User 1",
            email="user1@example.com",
            rating=5,
            comment="Great product, highly recommended!"
        )
        repo.create(
            name="User 2",
            email="user2@example.com",
            rating=4,
            comment="Very good, but could be better."
        )

        # List pending reviews
        pending_reviews = repo.list_by_status(status="pending", limit=10)

        assert len(pending_reviews) == 2
        assert all(r["status"] == "pending" for r in pending_reviews)

    def test_list_by_status_approved(self, mock_dynamodb_table):
        """Test List Reviews by Status (approved)."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create and approve review
        review = repo.create(
            name="Approved User",
            email="approved@example.com",
            rating=5,
            comment="This is an approved review for testing."
        )

        repo.update_status(
            review_id=review["id"],
            status="approved",
            admin_user_id="admin123"
        )

        # List approved reviews
        approved_reviews = repo.list_by_status(status="approved", limit=10)

        assert len(approved_reviews) == 1
        assert approved_reviews[0]["status"] == "approved"

    def test_list_by_status_newest_first(self, mock_dynamodb_table):
        """Test List Reviews (newest first = DESC)."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        import time

        # Create reviews mit zeitlichem Abstand
        review1 = repo.create(
            name="First User",
            email="first@example.com",
            rating=5,
            comment="First review created for testing."
        )
        time.sleep(0.01)  # Kurze Pause für unterschiedliche Timestamps

        review2 = repo.create(
            name="Second User",
            email="second@example.com",
            rating=4,
            comment="Second review created for testing."
        )

        # List newest first (scan_index_forward=False)
        reviews = repo.list_by_status(
            status="pending",
            limit=10,
            scan_index_forward=False
        )

        assert len(reviews) >= 2
        # Neueste zuerst
        assert reviews[0]["id"] == review2["id"]
        assert reviews[1]["id"] == review1["id"]

    def test_list_by_rating(self, mock_dynamodb_table):
        """Test List Reviews by Rating."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create reviews mit verschiedenen Ratings
        repo.create(
            name="5-Star User",
            email="5star@example.com",
            rating=5,
            comment="Absolutely perfect product!"
        )
        repo.create(
            name="4-Star User",
            email="4star@example.com",
            rating=4,
            comment="Very good product overall."
        )
        repo.create(
            name="Another 5-Star",
            email="another5@example.com",
            rating=5,
            comment="Another perfect review here."
        )

        # List 5-star reviews
        five_star_reviews = repo.list_by_rating(rating=5, limit=10)

        assert len(five_star_reviews) == 2
        assert all(r["rating"] == 5 for r in five_star_reviews)

    def test_update_status_to_approved(self, mock_dynamodb_table):
        """Test Update Review Status to Approved."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create review
        review = repo.create(
            name="Test User",
            email="test@example.com",
            rating=5,
            comment="Test review for approval."
        )

        # Approve review
        updated = repo.update_status(
            review_id=review["id"],
            status="approved",
            admin_user_id="admin123"
        )

        assert updated is not None
        assert updated["status"] == "approved"
        assert updated["approved_by"] == "admin123"
        assert "approved_at" in updated
        assert updated["GSI1PK"] == "review_status#approved"

    def test_update_status_to_rejected(self, mock_dynamodb_table):
        """Test Update Review Status to Rejected."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create review
        review = repo.create(
            name="Test User",
            email="test@example.com",
            rating=2,
            comment="This review will be rejected for testing."
        )

        # Reject review
        updated = repo.update_status(
            review_id=review["id"],
            status="rejected",
            admin_user_id="admin456",
            rejected_reason="Nicht relevant"
        )

        assert updated is not None
        assert updated["status"] == "rejected"
        assert updated["rejected_by"] == "admin456"
        assert updated["rejected_reason"] == "Nicht relevant"
        assert "rejected_at" in updated
        assert updated["GSI1PK"] == "review_status#rejected"

    def test_update_status_not_found(self, mock_dynamodb_table):
        """Test Update Status for Non-Existent Review."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        result = repo.update_status(
            review_id=uuid4(),
            status="approved",
            admin_user_id="admin123"
        )

        assert result is None

    def test_bulk_update_status(self, mock_dynamodb_table):
        """Test Bulk Update Review Status."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create multiple reviews
        review1 = repo.create(
            name="User 1",
            email="user1@example.com",
            rating=5,
            comment="Great product for bulk approval test."
        )
        review2 = repo.create(
            name="User 2",
            email="user2@example.com",
            rating=4,
            comment="Good product for bulk approval test."
        )
        review3 = repo.create(
            name="User 3",
            email="user3@example.com",
            rating=5,
            comment="Excellent product for bulk approval test."
        )

        review_ids = [review1["id"], review2["id"], review3["id"]]

        # Bulk approve
        success_count = repo.bulk_update_status(
            review_ids=review_ids,
            status="approved",
            admin_user_id="admin_bulk"
        )

        assert success_count == 3

        # Verify all approved
        for review_id in review_ids:
            review = repo.get(review_id)
            assert review["status"] == "approved"
            assert review["approved_by"] == "admin_bulk"

    def test_bulk_update_status_partial_failure(self, mock_dynamodb_table):
        """Test Bulk Update mit teilweise nicht existierenden Reviews."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create one review
        review1 = repo.create(
            name="Existing User",
            email="existing@example.com",
            rating=5,
            comment="This review exists for partial bulk test."
        )

        # Non-existent review
        fake_id = uuid4()

        review_ids = [review1["id"], fake_id]

        # Bulk approve
        success_count = repo.bulk_update_status(
            review_ids=review_ids,
            status="approved",
            admin_user_id="admin_bulk"
        )

        assert success_count == 1  # Only 1 succeeded

    def test_get_rating_stats_empty(self, mock_dynamodb_table):
        """Test Rating Stats wenn keine approved reviews."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        stats = repo.get_rating_stats()

        assert stats["average"] == 0.0
        assert stats["count"] == 0
        assert stats["distribution"] == {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    def test_get_rating_stats_with_reviews(self, mock_dynamodb_table):
        """Test Rating Stats mit approved reviews."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create and approve reviews
        reviews = [
            repo.create("User1", "user1@example.com", 5, "Excellent product, highly recommended!"),
            repo.create("User2", "user2@example.com", 5, "Amazing product, best purchase ever!"),
            repo.create("User3", "user3@example.com", 4, "Very good product, minor improvements needed."),
            repo.create("User4", "user4@example.com", 3, "Okay product, meets basic expectations."),
            repo.create("User5", "user5@example.com", 5, "Perfect product, absolutely love it!"),
        ]

        # Approve all
        for review in reviews:
            repo.update_status(review["id"], "approved", "admin123")

        stats = repo.get_rating_stats()

        assert stats["count"] == 5
        assert float(stats["average"]) == 4.4  # (5+5+4+3+5) / 5 = 4.4
        assert stats["distribution"] == {1: 0, 2: 0, 3: 1, 4: 1, 5: 3}

    def test_get_rating_stats_only_approved(self, mock_dynamodb_table):
        """Test dass Rating Stats nur approved reviews berücksichtigt."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create reviews (some approved, some pending)
        review1 = repo.create("User1", "user1@example.com", 5, "Approved 5-star review for testing.")
        review2 = repo.create("User2", "user2@example.com", 1, "Pending 1-star review for testing.")

        # Nur Review 1 approven
        repo.update_status(review1["id"], "approved", "admin123")

        stats = repo.get_rating_stats()

        # Nur approved review (5 Sterne) sollte gezählt werden
        assert stats["count"] == 1
        assert float(stats["average"]) == 5.0
        assert stats["distribution"] == {1: 0, 2: 0, 3: 0, 4: 0, 5: 1}

    def test_delete_review(self, mock_dynamodb_table):
        """Test Review Deletion."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Create review
        review = repo.create(
            name="Delete User",
            email="delete@example.com",
            rating=3,
            comment="This review will be deleted for testing."
        )

        review_id = review["id"]

        # Delete review
        deleted = repo.delete(review_id)

        assert deleted is True

        # Verify deletion
        retrieved = repo.get(review_id)
        assert retrieved is None

    def test_delete_review_not_found(self, mock_dynamodb_table):
        """Test Delete Non-Existent Review."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        # Note: DynamoDB delete returns success even if item doesn't exist
        # This is expected DynamoDB behavior (idempotent delete)
        deleted = repo.delete(uuid4())

        assert deleted is True  # DynamoDB delete is idempotent


class TestSpamDetection:
    """Tests für Spam Detection Logic."""

    def test_spam_detection_too_many_urls(self, mock_dynamodb_table):
        """Test Spam Detection: Zu viele URLs."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        review = repo.create(
            name="Spammer",
            email="spam@example.com",
            rating=5,
            comment="Great product! Visit http://spam1.com and http://spam2.com and http://spam3.com"
        )

        assert review["status"] == "spam"
        assert review["is_spam"] is True
        assert review["GSI1PK"] == "review_status#spam"

    def test_spam_detection_too_short(self, mock_dynamodb_table):
        """Test Spam Detection: Kommentar zu kurz."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        review = repo.create(
            name="Short User",
            email="short@example.com",
            rating=5,
            comment="Good"  # Nur 4 Zeichen
        )

        assert review["status"] == "spam"
        assert review["is_spam"] is True

    def test_spam_detection_too_long(self, mock_dynamodb_table):
        """Test Spam Detection: Kommentar zu lang."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        long_comment = "x" * 501  # Mehr als 500 Zeichen

        review = repo.create(
            name="Verbose User",
            email="verbose@example.com",
            rating=5,
            comment=long_comment
        )

        assert review["status"] == "spam"
        assert review["is_spam"] is True

    def test_spam_detection_all_caps(self, mock_dynamodb_table):
        """Test Spam Detection: Alles in Großbuchstaben."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        review = repo.create(
            name="Caps User",
            email="caps@example.com",
            rating=5,
            comment="THIS IS AN ALL CAPS COMMENT WHICH IS SPAM"
        )

        assert review["status"] == "spam"
        assert review["is_spam"] is True

    def test_spam_detection_excessive_caps(self, mock_dynamodb_table):
        """Test Spam Detection: Zu viele Großbuchstaben (>50%)."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        review = repo.create(
            name="Excessive Caps User",
            email="excessivecaps@example.com",
            rating=5,
            comment="THIS IS A COMMENT WITH MORE THAN FIFTY PERCENT CAPS"
        )

        assert review["status"] == "spam"
        assert review["is_spam"] is True

    def test_no_spam_valid_comment(self, mock_dynamodb_table):
        """Test dass valide Comments nicht als Spam erkannt werden."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        review = repo.create(
            name="Valid User",
            email="valid@example.com",
            rating=5,
            comment="This is a perfectly valid review with normal text."
        )

        assert review["status"] == "pending"
        assert review["is_spam"] is False

    def test_no_spam_one_url(self, mock_dynamodb_table):
        """Test dass 1-2 URLs erlaubt sind."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        review = repo.create(
            name="URL User",
            email="url@example.com",
            rating=5,
            comment="Great product! Check it out at https://example.com for more info."
        )

        assert review["status"] == "pending"
        assert review["is_spam"] is False

    def test_no_spam_normal_caps(self, mock_dynamodb_table):
        """Test dass normale Caps-Nutzung erlaubt ist."""
        repo = ReviewRepository(table=mock_dynamodb_table)

        review = repo.create(
            name="Normal Caps User",
            email="normalcaps@example.com",
            rating=5,
            comment="This is a Great Product with Normal Capitalization!"
        )

        assert review["status"] == "pending"
        assert review["is_spam"] is False
