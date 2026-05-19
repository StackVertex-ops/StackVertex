"""Unit Tests für Feedback Repository."""

import pytest
from datetime import datetime
from uuid import uuid4
from moto import mock_aws
import boto3

from app.repositories.feedback import FeedbackRepository


@pytest.fixture
def dynamodb_table():
    """Create mock DynamoDB table."""
    with mock_aws():
        # Create DynamoDB resource
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

        # Create table mit allen GSIs
        table = dynamodb.create_table(
            TableName='overcloud-test',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI2PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI2SK', 'AttributeType': 'S'},
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'GSI2',
                    'KeySchema': [
                        {'AttributeName': 'GSI2PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI2SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        yield table


@pytest.fixture
def feedback_repo(dynamodb_table):
    """Create FeedbackRepository instance."""
    return FeedbackRepository(table=dynamodb_table)


# ============================================================================
# Create Feedback Tests
# ============================================================================


def test_create_feedback_minimal(feedback_repo):
    """Test Feedback-Erstellung mit minimalen Daten."""
    feedback = feedback_repo.create_feedback(
        feedback_type="bug",
        title="Button kaputt",
        description="Der Submit-Button funktioniert nicht mehr."
    )

    assert feedback["feedback_id"] is not None
    assert feedback["type"] == "bug"
    assert feedback["status"] == "new"
    assert feedback["title"] == "Button kaputt"
    assert feedback["description"] == "Der Submit-Button funktioniert nicht mehr."
    assert feedback["email"] is None
    assert feedback["screenshot_s3_key"] is None
    assert feedback["is_resolved"] is False
    assert feedback["resolved_at"] is None
    assert feedback["notes"] == []
    assert feedback["entity_type"] == "feedback"


def test_create_feedback_with_email(feedback_repo):
    """Test Feedback mit Email."""
    feedback = feedback_repo.create_feedback(
        feedback_type="feature",
        title="Dark Mode bitte",
        description="Ich hätte gerne einen Dark Mode.",
        email="user@example.com"
    )

    assert feedback["email"] == "user@example.com"


def test_create_feedback_with_screenshot(feedback_repo):
    """Test Feedback mit Screenshot."""
    feedback = feedback_repo.create_feedback(
        feedback_type="bug",
        title="Layout broken",
        description="Layout ist kaputt",
        screenshot_s3_key="feedback/screenshots/2026/05/19/error.png"
    )

    assert feedback["screenshot_s3_key"] == "feedback/screenshots/2026/05/19/error.png"


def test_create_feedback_with_browser_info(feedback_repo):
    """Test Feedback mit Browser-Info."""
    browser_info = {
        "browser": "Chrome",
        "version": "120.0.0",
        "os": "macOS"
    }

    feedback = feedback_repo.create_feedback(
        feedback_type="bug",
        title="Render Issue",
        description="Rendering problem in Chrome",
        url="https://app.overcloud.dev/dashboard",
        user_agent="Mozilla/5.0 ...",
        browser_info=browser_info
    )

    assert feedback["url"] == "https://app.overcloud.dev/dashboard"
    assert feedback["user_agent"] == "Mozilla/5.0 ..."
    assert feedback["browser_info"]["browser"] == "Chrome"


def test_create_feedback_all_types(feedback_repo):
    """Test alle Feedback-Typen."""
    types = ["bug", "feature", "feedback", "other"]

    for feedback_type in types:
        feedback = feedback_repo.create_feedback(
            feedback_type=feedback_type,
            title=f"Test {feedback_type}",
            description=f"Testing {feedback_type} type"
        )

        assert feedback["type"] == feedback_type
        # GSI1PK für Status-Filter (initial status is always "new")
        assert feedback["GSI1PK"] == "feedback_status#new"
        # GSI2PK für Type-Filter
        assert feedback["GSI2PK"] == f"feedback_type#{feedback_type}"


# ============================================================================
# Get Feedback Tests
# ============================================================================


def test_get_feedback_success(feedback_repo):
    """Test Feedback abrufen."""
    created = feedback_repo.create_feedback(
        feedback_type="bug",
        title="Test Bug",
        description="Test description"
    )

    feedback = feedback_repo.get_feedback(created["feedback_id"])

    assert feedback is not None
    assert feedback["feedback_id"] == created["feedback_id"]
    assert feedback["title"] == "Test Bug"


def test_get_feedback_not_found(feedback_repo):
    """Test Feedback nicht gefunden."""
    feedback = feedback_repo.get_feedback("non-existent-id")

    assert feedback is None


# ============================================================================
# List Feedback Tests
# ============================================================================


def test_list_feedback_all(feedback_repo):
    """Test alle Feedbacks abrufen."""
    # Create test feedbacks
    feedback_repo.create_feedback(
        feedback_type="bug",
        title="Bug 1",
        description="Description 1"
    )
    feedback_repo.create_feedback(
        feedback_type="feature",
        title="Feature 1",
        description="Description 2"
    )
    feedback_repo.create_feedback(
        feedback_type="feedback",
        title="Feedback 1",
        description="Description 3"
    )

    items, last_key = feedback_repo.list_feedback()

    assert len(items) == 3
    # Sorted by created_at DESC (newest first)
    assert items[0]["title"] == "Feedback 1"
    assert last_key is None


def test_list_feedback_filter_by_status(feedback_repo):
    """Test Feedback-Liste nach Status filtern."""
    # Create feedback with different statuses
    fb1 = feedback_repo.create_feedback(
        feedback_type="bug",
        title="New Bug",
        description="New bug report"
    )

    fb2 = feedback_repo.create_feedback(
        feedback_type="bug",
        title="In Progress Bug",
        description="Bug being worked on"
    )
    feedback_repo.update_feedback(fb2["feedback_id"], status="in_progress")

    fb3 = feedback_repo.create_feedback(
        feedback_type="bug",
        title="Another New Bug",
        description="Another new bug"
    )

    # Filter by status "new"
    items, _ = feedback_repo.list_feedback(status="new")

    assert len(items) == 2
    assert all(item["status"] == "new" for item in items)


def test_list_feedback_filter_by_type(feedback_repo):
    """Test Feedback-Liste nach Type filtern."""
    # Create feedbacks of different types
    feedback_repo.create_feedback(
        feedback_type="bug",
        title="Bug 1",
        description="Bug description"
    )
    feedback_repo.create_feedback(
        feedback_type="feature",
        title="Feature 1",
        description="Feature description"
    )
    feedback_repo.create_feedback(
        feedback_type="bug",
        title="Bug 2",
        description="Another bug"
    )

    # Filter by type "bug"
    items, _ = feedback_repo.list_feedback(feedback_type="bug")

    assert len(items) == 2
    assert all(item["type"] == "bug" for item in items)


def test_list_feedback_with_limit(feedback_repo):
    """Test Pagination mit Limit."""
    # Create 5 feedbacks
    for i in range(5):
        feedback_repo.create_feedback(
            feedback_type="bug",
            title=f"Bug {i}",
            description=f"Description {i}"
        )

    # Request only 3
    items, last_key = feedback_repo.list_feedback(limit=3)

    assert len(items) <= 3


# ============================================================================
# Update Feedback Tests
# ============================================================================


def test_update_feedback_status(feedback_repo):
    """Test Feedback-Status ändern."""
    feedback = feedback_repo.create_feedback(
        feedback_type="bug",
        title="Test Bug",
        description="Test description"
    )

    # Update status to in_progress
    updated = feedback_repo.update_feedback(
        feedback_id=feedback["feedback_id"],
        status="in_progress"
    )

    assert updated is not None
    assert updated["status"] == "in_progress"
    # GSI1PK should be updated for status filter
    assert updated["GSI1PK"] == "feedback_status#in_progress"


def test_update_feedback_mark_resolved(feedback_repo):
    """Test Feedback als resolved markieren."""
    feedback = feedback_repo.create_feedback(
        feedback_type="bug",
        title="Test Bug",
        description="Test description"
    )

    admin_id = str(uuid4())

    # Mark as resolved
    updated = feedback_repo.update_feedback(
        feedback_id=feedback["feedback_id"],
        is_resolved=True,
        resolved_by=admin_id
    )

    assert updated is not None
    assert updated["is_resolved"] is True
    assert updated["resolved_by"] == admin_id
    assert updated["resolved_at"] is not None


def test_update_feedback_not_found(feedback_repo):
    """Test Update für nicht-existierendes Feedback."""
    updated = feedback_repo.update_feedback(
        feedback_id="non-existent-id",
        status="closed"
    )

    assert updated is None


# ============================================================================
# Notes Management Tests
# ============================================================================


def test_add_note(feedback_repo):
    """Test Notiz zu Feedback hinzufügen."""
    feedback = feedback_repo.create_feedback(
        feedback_type="bug",
        title="Test Bug",
        description="Test description"
    )

    admin_id = str(uuid4())
    admin_email = "admin@overcloud.dev"

    # Add note
    updated = feedback_repo.add_note(
        feedback_id=feedback["feedback_id"],
        admin_id=admin_id,
        admin_email=admin_email,
        note="We are looking into this issue."
    )

    assert updated is not None
    assert len(updated["notes"]) == 1

    note = updated["notes"][0]
    assert note["note_id"] is not None
    assert note["admin_id"] == admin_id
    assert note["admin_email"] == admin_email
    assert note["note"] == "We are looking into this issue."
    assert note["created_at"] is not None


def test_add_multiple_notes(feedback_repo):
    """Test mehrere Notizen hinzufügen."""
    feedback = feedback_repo.create_feedback(
        feedback_type="bug",
        title="Test Bug",
        description="Test description"
    )

    admin_id = str(uuid4())

    # Add first note
    feedback_repo.add_note(
        feedback_id=feedback["feedback_id"],
        admin_id=admin_id,
        admin_email="admin@overcloud.dev",
        note="First note"
    )

    # Add second note
    updated = feedback_repo.add_note(
        feedback_id=feedback["feedback_id"],
        admin_id=admin_id,
        admin_email="admin@overcloud.dev",
        note="Second note"
    )

    assert len(updated["notes"]) == 2
    assert updated["notes"][0]["note"] == "First note"
    assert updated["notes"][1]["note"] == "Second note"


def test_add_note_not_found(feedback_repo):
    """Test Notiz zu nicht-existierendem Feedback."""
    updated = feedback_repo.add_note(
        feedback_id="non-existent-id",
        admin_id=str(uuid4()),
        admin_email="admin@overcloud.dev",
        note="This should fail"
    )

    assert updated is None


# ============================================================================
# Mark Resolved Tests
# ============================================================================


def test_mark_resolved(feedback_repo):
    """Test Feedback als resolved markieren mit Resolution-Note."""
    feedback = feedback_repo.create_feedback(
        feedback_type="bug",
        title="Test Bug",
        description="Test description"
    )

    admin_id = str(uuid4())
    admin_email = "admin@overcloud.dev"

    # Mark as resolved
    resolved = feedback_repo.mark_resolved(
        feedback_id=feedback["feedback_id"],
        admin_id=admin_id,
        admin_email=admin_email,
        resolution_note="Fixed in version 1.2.0"
    )

    assert resolved is not None
    assert resolved["status"] == "resolved"
    assert resolved["is_resolved"] is True
    assert resolved["resolved_by"] == admin_id
    assert resolved["resolved_at"] is not None
    assert resolved["GSI1PK"] == "feedback_status#resolved"

    # Verify resolution note was added
    assert len(resolved["notes"]) == 1
    assert "RESOLVED" in resolved["notes"][0]["note"]
    assert "Fixed in version 1.2.0" in resolved["notes"][0]["note"]


def test_mark_resolved_not_found(feedback_repo):
    """Test mark_resolved für nicht-existierendes Feedback."""
    resolved = feedback_repo.mark_resolved(
        feedback_id="non-existent-id",
        admin_id=str(uuid4()),
        admin_email="admin@overcloud.dev",
        resolution_note="This should fail"
    )

    assert resolved is None


# ============================================================================
# Statistics Tests
# ============================================================================


def test_get_stats_empty(feedback_repo):
    """Test Statistiken für leere Datenbank."""
    stats = feedback_repo.get_stats()

    assert stats["total"] == 0
    assert stats["unresolved"] == 0
    assert stats["by_status"]["new"] == 0
    assert stats["by_type"]["bug"] == 0


def test_get_stats_with_data(feedback_repo):
    """Test Statistiken mit Feedback-Daten."""
    # Create various feedbacks
    feedback_repo.create_feedback(
        feedback_type="bug",
        title="Bug 1",
        description="Bug description"
    )

    fb2 = feedback_repo.create_feedback(
        feedback_type="bug",
        title="Bug 2",
        description="Bug description"
    )
    feedback_repo.update_feedback(fb2["feedback_id"], status="in_progress")

    fb3 = feedback_repo.create_feedback(
        feedback_type="feature",
        title="Feature 1",
        description="Feature description"
    )
    feedback_repo.mark_resolved(
        feedback_id=fb3["feedback_id"],
        admin_id=str(uuid4()),
        admin_email="admin@overcloud.dev",
        resolution_note="Done"
    )

    feedback_repo.create_feedback(
        feedback_type="feedback",
        title="Feedback 1",
        description="General feedback"
    )

    stats = feedback_repo.get_stats()

    assert stats["total"] == 4
    assert stats["unresolved"] == 3  # Only fb3 is resolved
    assert stats["by_status"]["new"] == 2  # fb1 and fb4
    assert stats["by_status"]["in_progress"] == 1  # fb2
    assert stats["by_status"]["resolved"] == 1  # fb3
    assert stats["by_type"]["bug"] == 2
    assert stats["by_type"]["feature"] == 1
    assert stats["by_type"]["feedback"] == 1


def test_get_stats_all_statuses(feedback_repo):
    """Test Statistiken mit allen Status-Typen."""
    # Create feedbacks with all statuses
    fb1 = feedback_repo.create_feedback(
        feedback_type="bug",
        title="New",
        description="New feedback"
    )

    fb2 = feedback_repo.create_feedback(
        feedback_type="bug",
        title="In Progress",
        description="In progress feedback"
    )
    feedback_repo.update_feedback(fb2["feedback_id"], status="in_progress")

    fb3 = feedback_repo.create_feedback(
        feedback_type="bug",
        title="Resolved",
        description="Resolved feedback"
    )
    feedback_repo.update_feedback(fb3["feedback_id"], status="resolved", is_resolved=True)

    fb4 = feedback_repo.create_feedback(
        feedback_type="bug",
        title="Closed",
        description="Closed feedback"
    )
    feedback_repo.update_feedback(fb4["feedback_id"], status="closed")

    stats = feedback_repo.get_stats()

    assert stats["total"] == 4
    assert stats["by_status"]["new"] == 1
    assert stats["by_status"]["in_progress"] == 1
    assert stats["by_status"]["resolved"] == 1
    assert stats["by_status"]["closed"] == 1
