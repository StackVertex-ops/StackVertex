"""Unit Tests für ReviewService.

Tests für:
- Review Submission (public)
- Spam Detection Integration
- Public Reviews Retrieval
- Admin Moderation (approve, reject, spam)
- Bulk Operations
- Rating Summary
"""

import pytest
from uuid import uuid4

from app.repositories.review import ReviewRepository
from app.services.review_service import ReviewService


class TestReviewServiceSubmission:
    """Tests für Review Submission."""

    @pytest.mark.asyncio
    async def test_submit_review_valid(self, mock_dynamodb_table):
        """Test Submit Valid Review."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        review = await service.submit_review(
            name="Max Mustermann",
            email="max@example.com",
            rating=5,
            comment="Sehr gutes Produkt! Bin sehr zufrieden damit."
        )

        assert review["name"] == "Max Mustermann"
        assert review["email"] == "max@example.com"
        assert review["rating"] == 5
        assert review["status"] == "pending"
        assert review["is_spam"] is False

    @pytest.mark.asyncio

    async def test_submit_review_with_metadata(self, mock_dynamodb_table):
        """Test Submit Review mit IP und User-Agent."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        review = await service.submit_review(
            name="Anna Schmidt",
            email="anna@example.com",
            rating=4,
            comment="Gutes Produkt mit kleinen Verbesserungsmöglichkeiten.",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )

        assert review["ip_address"] == "192.168.1.1"
        assert review["user_agent"] == "Mozilla/5.0"

    @pytest.mark.asyncio

    async def test_submit_review_invalid_rating_too_low(self, mock_dynamodb_table):
        """Test Submit Review mit Rating < 1."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        with pytest.raises(ValueError, match="Rating muss zwischen 1 und 5 liegen"):
            await service.submit_review(
                name="Test User",
                email="test@example.com",
                rating=0,
                comment="This review has invalid rating (too low)."
            )

    @pytest.mark.asyncio

    async def test_submit_review_invalid_rating_too_high(self, mock_dynamodb_table):
        """Test Submit Review mit Rating > 5."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        with pytest.raises(ValueError, match="Rating muss zwischen 1 und 5 liegen"):
            await service.submit_review(
                name="Test User",
                email="test@example.com",
                rating=6,
                comment="This review has invalid rating (too high)."
            )

    @pytest.mark.asyncio

    async def test_submit_review_comment_too_short(self, mock_dynamodb_table):
        """Test Submit Review mit zu kurzem Kommentar."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        with pytest.raises(ValueError, match="Kommentar muss mindestens 10 Zeichen lang sein"):
            await service.submit_review(
                name="Test User",
                email="test@example.com",
                rating=5,
                comment="Short"  # Nur 5 Zeichen
            )

    @pytest.mark.asyncio

    async def test_submit_review_comment_too_long(self, mock_dynamodb_table):
        """Test Submit Review mit zu langem Kommentar."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        long_comment = "x" * 501  # > 500 Zeichen

        with pytest.raises(ValueError, match="Kommentar darf maximal 500 Zeichen lang sein"):
            await service.submit_review(
                name="Test User",
                email="test@example.com",
                rating=5,
                comment=long_comment
            )


class TestReviewServiceSpamDetection:
    """Tests für Spam Detection Integration."""

    @pytest.mark.asyncio

    async def test_submit_review_spam_detected(self, mock_dynamodb_table):
        """Test dass Spam automatisch als spam markiert wird."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        # Submit review mit vielen URLs (Spam)
        review = await service.submit_review(
            name="Spammer",
            email="spam@example.com",
            rating=5,
            comment="Visit http://spam1.com and http://spam2.com and http://spam3.com"
        )

        assert review["status"] == "spam"
        assert review["is_spam"] is True

    @pytest.mark.asyncio

    async def test_submit_review_no_spam(self, mock_dynamodb_table):
        """Test dass valide Reviews als pending markiert werden."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        review = await service.submit_review(
            name="Valid User",
            email="valid@example.com",
            rating=5,
            comment="This is a perfectly normal review without spam indicators."
        )

        assert review["status"] == "pending"
        assert review["is_spam"] is False


class TestReviewServicePublicReviews:
    """Tests für Public Reviews Retrieval."""

    @pytest.mark.asyncio

    async def test_get_public_reviews_empty(self, mock_dynamodb_table):
        """Test Get Public Reviews wenn keine approved reviews."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        result = await service.get_public_reviews(limit=20)

        assert result["reviews"] == []
        assert result["stats"]["count"] == 0
        assert result["stats"]["average"] == 0.0

    @pytest.mark.asyncio

    async def test_get_public_reviews_only_approved(self, mock_dynamodb_table):
        """Test dass nur approved reviews zurückgegeben werden."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        # Create reviews
        review1 = await service.submit_review(
            "User1", "user1@example.com", 5, "Approved review for public display test."
        )
        review2 = await service.submit_review(
            "User2", "user2@example.com", 4, "Pending review that should not appear."
        )

        # Approve nur Review 1
        repo.update_status(review1["id"], "approved", "admin123")

        # Get public reviews
        result = await service.get_public_reviews(limit=20)

        assert len(result["reviews"]) == 1
        assert result["reviews"][0]["id"] == review1["id"]

    @pytest.mark.asyncio

    async def test_get_public_reviews_no_private_fields(self, mock_dynamodb_table):
        """Test dass private Felder (email, IP) nicht zurückgegeben werden."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        # Create and approve review
        review = await service.submit_review(
            name="Public User",
            email="public@example.com",
            rating=5,
            comment="This review should be public without private data.",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        repo.update_status(review["id"], "approved", "admin123")

        # Get public reviews
        result = await service.get_public_reviews(limit=20)

        public_review = result["reviews"][0]

        # Public fields should exist
        assert "id" in public_review
        assert "name" in public_review
        assert "rating" in public_review
        assert "comment" in public_review
        assert "created_at" in public_review

        # Private fields should NOT exist
        assert "email" not in public_review
        assert "ip_address" not in public_review
        assert "user_agent" not in public_review
        assert "status" not in public_review

    @pytest.mark.asyncio

    async def test_get_public_reviews_with_stats(self, mock_dynamodb_table):
        """Test Get Public Reviews mit Rating Stats."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        # Create and approve reviews
        reviews = [
            await service.submit_review("User1", "user1@example.com", 5, "Perfect product, excellent quality!"),
            await service.submit_review("User2", "user2@example.com", 4, "Very good product, highly recommend."),
            await service.submit_review("User3", "user3@example.com", 5, "Amazing product, best purchase!"),
        ]

        for review in reviews:
            repo.update_status(review["id"], "approved", "admin123")

        # Get public reviews
        result = await service.get_public_reviews(limit=20)

        assert len(result["reviews"]) == 3
        assert result["stats"]["count"] == 3
        assert float(result["stats"]["average"]) == pytest.approx(4.67, rel=0.01)
        assert result["stats"]["distribution"][5] == 2
        assert result["stats"]["distribution"][4] == 1

    @pytest.mark.asyncio

    async def test_get_public_reviews_limit(self, mock_dynamodb_table):
        """Test Get Public Reviews mit Limit."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        # Create and approve many reviews
        for i in range(10):
            review = await service.submit_review(
                f"User{i}",
                f"user{i}@example.com",
                5,
                f"Review number {i} for testing limit functionality."
            )
            repo.update_status(review["id"], "approved", "admin123")

        # Get only 5 reviews
        result = await service.get_public_reviews(limit=5)

        assert len(result["reviews"]) == 5


class TestReviewServiceModeration:
    """Tests für Admin Moderation."""

    @pytest.mark.asyncio

    async def test_get_reviews_for_moderation_all(self, mock_dynamodb_table):
        """Test Get All Reviews für Moderation (alle Status)."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        # Create reviews mit verschiedenen Status
        review1 = await service.submit_review("User1", "user1@example.com", 5, "Pending review for moderation test.")
        review2 = await service.submit_review("User2", "user2@example.com", 4, "Another pending review for moderation.")

        repo.update_status(review2["id"], "approved", "admin123")

        # Get all reviews
        all_reviews = await service.get_reviews_for_moderation(status=None, limit=100)

        assert len(all_reviews) == 2

    @pytest.mark.asyncio

    async def test_get_reviews_for_moderation_filtered(self, mock_dynamodb_table):
        """Test Get Reviews für Moderation (gefiltert nach Status)."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        # Create reviews
        review1 = await service.submit_review("User1", "user1@example.com", 5, "Pending review number one.")
        review2 = await service.submit_review("User2", "user2@example.com", 4, "Pending review number two.")

        repo.update_status(review2["id"], "approved", "admin123")

        # Get only pending reviews
        pending_reviews = await service.get_reviews_for_moderation(status="pending", limit=100)

        assert len(pending_reviews) == 1
        assert pending_reviews[0]["id"] == review1["id"]

    @pytest.mark.asyncio

    async def test_approve_review(self, mock_dynamodb_table):
        """Test Approve Review."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        # Create review
        review = await service.submit_review(
            "Test User",
            "test@example.com",
            5,
            "This review will be approved for testing."
        )

        # Approve
        updated = await service.approve_review(
            review_id=review["id"],
            admin_user_id="admin123"
        )

        assert updated["status"] == "approved"
        assert updated["approved_by"] == "admin123"
        assert "approved_at" in updated

    @pytest.mark.asyncio

    async def test_approve_review_not_found(self, mock_dynamodb_table):
        """Test Approve Non-Existent Review."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        with pytest.raises(ValueError, match="nicht gefunden"):
            await service.approve_review(
                review_id=uuid4(),
                admin_user_id="admin123"
            )

    @pytest.mark.asyncio

    async def test_reject_review(self, mock_dynamodb_table):
        """Test Reject Review."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        # Create review
        review = await service.submit_review(
            "Test User",
            "test@example.com",
            2,
            "This review will be rejected for testing."
        )

        # Reject
        updated = await service.reject_review(
            review_id=review["id"],
            admin_user_id="admin456",
            reason="Nicht relevant"
        )

        assert updated["status"] == "rejected"
        assert updated["rejected_by"] == "admin456"
        assert updated["rejected_reason"] == "Nicht relevant"
        assert "rejected_at" in updated

    @pytest.mark.asyncio

    async def test_reject_review_without_reason(self, mock_dynamodb_table):
        """Test Reject Review ohne Grund."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        # Create review
        review = await service.submit_review(
            "Test User",
            "test@example.com",
            3,
            "This review will be rejected without reason."
        )

        # Reject without reason
        updated = await service.reject_review(
            review_id=review["id"],
            admin_user_id="admin456"
        )

        assert updated["status"] == "rejected"
        assert "rejected_reason" not in updated

    @pytest.mark.asyncio

    async def test_reject_review_not_found(self, mock_dynamodb_table):
        """Test Reject Non-Existent Review."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        with pytest.raises(ValueError, match="nicht gefunden"):
            await service.reject_review(
                review_id=uuid4(),
                admin_user_id="admin456"
            )

    @pytest.mark.asyncio

    async def test_mark_spam(self, mock_dynamodb_table):
        """Test Mark Review as Spam."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        # Create review (nicht automatisch als Spam erkannt)
        review = await service.submit_review(
            "Test User",
            "test@example.com",
            5,
            "This is a normal review that admin marks as spam."
        )

        # Mark as spam
        updated = await service.mark_spam(
            review_id=review["id"],
            admin_user_id="admin789"
        )

        assert updated["status"] == "spam"

    @pytest.mark.asyncio

    async def test_mark_spam_not_found(self, mock_dynamodb_table):
        """Test Mark Non-Existent Review as Spam."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        with pytest.raises(ValueError, match="nicht gefunden"):
            await service.mark_spam(
                review_id=uuid4(),
                admin_user_id="admin789"
            )


class TestReviewServiceBulkOperations:
    """Tests für Bulk Operations."""

    @pytest.mark.asyncio

    async def test_bulk_approve_all_success(self, mock_dynamodb_table):
        """Test Bulk Approve (alle erfolgreich)."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        # Create multiple reviews
        reviews = [
            await service.submit_review("User1", "user1@example.com", 5, "Review one for bulk approval test."),
            await service.submit_review("User2", "user2@example.com", 4, "Review two for bulk approval test."),
            await service.submit_review("User3", "user3@example.com", 5, "Review three for bulk approval test."),
        ]

        review_ids = [r["id"] for r in reviews]

        # Bulk approve
        result = await service.bulk_approve(
            review_ids=review_ids,
            admin_user_id="admin_bulk"
        )

        assert result["success_count"] == 3
        assert result["failed_count"] == 0
        assert result["total"] == 3

    @pytest.mark.asyncio

    async def test_bulk_approve_partial_failure(self, mock_dynamodb_table):
        """Test Bulk Approve mit teilweise nicht existierenden Reviews."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        # Create one review
        review = await service.submit_review(
            "Existing User",
            "existing@example.com",
            5,
            "This review exists for partial bulk test."
        )

        # Non-existent review
        fake_id = uuid4()

        review_ids = [review["id"], fake_id]

        # Bulk approve
        result = await service.bulk_approve(
            review_ids=review_ids,
            admin_user_id="admin_bulk"
        )

        assert result["success_count"] == 1
        assert result["failed_count"] == 1
        assert result["total"] == 2


class TestReviewServiceDeletion:
    """Tests für Review Deletion."""

    @pytest.mark.asyncio

    async def test_delete_review(self, mock_dynamodb_table):
        """Test Delete Review."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        # Create review
        review = await service.submit_review(
            "Delete User",
            "delete@example.com",
            3,
            "This review will be deleted for testing."
        )

        review_id = review["id"]

        # Delete
        deleted = await service.delete_review(
            review_id=review_id,
            admin_user_id="admin_delete"
        )

        assert deleted is True

        # Verify deletion
        assert repo.get(review_id) is None

    @pytest.mark.asyncio

    async def test_delete_review_not_found(self, mock_dynamodb_table):
        """Test Delete Non-Existent Review.

        Note: DynamoDB delete is idempotent - deleting a non-existent item
        returns success. The service layer doesn't check for existence before delete.
        """
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        # Note: delete_review doesn't raise ValueError für nicht-existierende Items
        # (DynamoDB delete ist idempotent)
        deleted = await service.delete_review(
            review_id=uuid4(),
            admin_user_id="admin_delete"
        )

        # DynamoDB delete returns True auch wenn Item nicht existiert
        assert deleted is True


class TestReviewServiceRatingSummary:
    """Tests für Rating Summary."""

    @pytest.mark.asyncio

    async def test_get_rating_summary_empty(self, mock_dynamodb_table):
        """Test Get Rating Summary ohne Reviews."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        stats = await service.get_rating_summary()

        assert stats["average"] == 0.0
        assert stats["count"] == 0
        assert stats["distribution"] == {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    @pytest.mark.asyncio

    async def test_get_rating_summary_with_approved_reviews(self, mock_dynamodb_table):
        """Test Get Rating Summary mit approved Reviews."""
        repo = ReviewRepository(table=mock_dynamodb_table)
        service = ReviewService(review_repository=repo)

        # Create and approve reviews
        reviews = [
            await service.submit_review("User1", "user1@example.com", 5, "Excellent product, best purchase ever!"),
            await service.submit_review("User2", "user2@example.com", 5, "Amazing product, highly recommended!"),
            await service.submit_review("User3", "user3@example.com", 4, "Very good product, minor improvements."),
            await service.submit_review("User4", "user4@example.com", 3, "Okay product, meets expectations."),
            await service.submit_review("User5", "user5@example.com", 5, "Perfect product, absolutely love it!"),
        ]

        # Approve all
        for review in reviews:
            repo.update_status(review["id"], "approved", "admin123")

        stats = await service.get_rating_summary()

        assert stats["count"] == 5
        assert float(stats["average"]) == 4.4  # (5+5+4+3+5) / 5 = 4.4
        assert stats["distribution"] == {1: 0, 2: 0, 3: 1, 4: 1, 5: 3}
