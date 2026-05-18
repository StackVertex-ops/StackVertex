"""Unit tests for RefreshTokenRepository."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, MagicMock

from app.repositories.refresh_token import RefreshTokenRepository


@pytest.fixture
def mock_table():
    """Mock DynamoDB table."""
    table = Mock()
    table.put_item = Mock()
    table.query = Mock()
    table.update_item = Mock()
    table.delete_item = Mock()
    table.scan = Mock()
    return table


@pytest.fixture
def refresh_token_repo(mock_table):
    """Create RefreshTokenRepository with mock table."""
    return RefreshTokenRepository(table=mock_table)


def test_create_refresh_token(refresh_token_repo, mock_table):
    """Test creating a refresh token."""
    user_id = uuid4()
    token = "test-jwt-token-here"
    expires_at = datetime.utcnow() + timedelta(days=7)

    # Mock put_item
    mock_table.put_item.return_value = None

    # Create token
    result = refresh_token_repo.create(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )

    # Verify
    assert "id" in result
    assert result["user_id"] == str(user_id)
    assert result["token_hash"] == refresh_token_repo._hash_token(token)
    assert result["revoked"] is False
    assert "ttl" in result
    mock_table.put_item.assert_called_once()


def test_get_by_token_success(refresh_token_repo, mock_table):
    """Test getting token by JWT (success)."""
    user_id = uuid4()
    token = "test-jwt-token"
    token_hash = refresh_token_repo._hash_token(token)

    # Mock query response
    mock_table.query.return_value = {
        "Items": [{
            "PK": f"USER#{user_id}",
            "SK": "REFRESH_TOKEN#123",
            "id": "123",
            "user_id": str(user_id),
            "token_hash": token_hash,
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "revoked": False
        }]
    }

    # Get token
    result = refresh_token_repo.get_by_token(token)

    # Verify
    assert result is not None
    assert result["id"] == "123"
    assert result["user_id"] == str(user_id)
    assert result["revoked"] is False


def test_get_by_token_expired(refresh_token_repo, mock_table):
    """Test getting expired token returns None."""
    token = "test-jwt-token"
    token_hash = refresh_token_repo._hash_token(token)

    # Mock query response (expired token)
    mock_table.query.return_value = {
        "Items": [{
            "id": "123",
            "token_hash": token_hash,
            "expires_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),  # Expired
            "revoked": False
        }]
    }

    # Get token
    result = refresh_token_repo.get_by_token(token)

    # Verify
    assert result is None


def test_get_by_token_revoked(refresh_token_repo, mock_table):
    """Test getting revoked token returns None."""
    token = "test-jwt-token"
    token_hash = refresh_token_repo._hash_token(token)

    # Mock query response (revoked token)
    mock_table.query.return_value = {
        "Items": [{
            "id": "123",
            "token_hash": token_hash,
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "revoked": True  # Revoked
        }]
    }

    # Get token
    result = refresh_token_repo.get_by_token(token)

    # Verify
    assert result is None


def test_get_by_token_not_found(refresh_token_repo, mock_table):
    """Test getting non-existent token returns None."""
    token = "test-jwt-token"

    # Mock query response (empty)
    mock_table.query.return_value = {"Items": []}

    # Get token
    result = refresh_token_repo.get_by_token(token)

    # Verify
    assert result is None


def test_revoke(refresh_token_repo, mock_table):
    """Test revoking a refresh token."""
    user_id = uuid4()
    token_id = "123"

    # Mock update_item
    mock_table.update_item.return_value = {
        "Attributes": {
            "id": token_id,
            "revoked": True
        }
    }

    # Revoke token
    result = refresh_token_repo.revoke(token_id, user_id)

    # Verify
    assert result["revoked"] is True
    mock_table.update_item.assert_called_once()


def test_revoke_all_for_user(refresh_token_repo, mock_table):
    """Test revoking all tokens for a user."""
    user_id = uuid4()

    # Mock query response (2 tokens)
    mock_table.query.return_value = {
        "Items": [
            {"PK": f"USER#{user_id}", "SK": "REFRESH_TOKEN#1", "revoked": False},
            {"PK": f"USER#{user_id}", "SK": "REFRESH_TOKEN#2", "revoked": False}
        ]
    }

    # Mock update_item
    mock_table.update_item.return_value = {"Attributes": {"revoked": True}}

    # Revoke all
    count = refresh_token_repo.revoke_all_for_user(user_id)

    # Verify
    assert count == 2
    assert mock_table.update_item.call_count == 2


def test_hash_token():
    """Test token hashing is consistent."""
    token = "test-token-123"
    hash1 = RefreshTokenRepository._hash_token(token)
    hash2 = RefreshTokenRepository._hash_token(token)

    # Same input = same hash
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex length

    # Different input = different hash
    hash3 = RefreshTokenRepository._hash_token("different-token")
    assert hash1 != hash3
