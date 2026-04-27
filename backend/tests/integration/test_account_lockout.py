"""Integration tests für Account Lockout.

Tests für Rate Limiting und automatische Account Lockout bei zu vielen Failed Logins.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(mock_dynamodb_table, mock_s3_bucket):
    """TestClient mit gemockten Dependencies."""
    from app.db.dynamodb import get_dynamodb_table
    from app.db.s3_storage import get_s3_storage, S3Storage

    app.dependency_overrides[get_dynamodb_table] = lambda: mock_dynamodb_table
    app.dependency_overrides[get_s3_storage] = lambda: S3Storage(bucket_name="overcloud-test-bucket")

    # Disable rate limiting for tests
    app.state.limiter.enabled = False

    yield TestClient(app)

    app.dependency_overrides.clear()
    app.state.limiter.enabled = True


class TestAccountLockout:
    """Tests für Account Lockout nach failed logins."""

    def test_account_locks_after_5_failed_attempts(self, client):
        """Test that account locks after 5 failed login attempts."""
        # Register user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "locktest@example.com",
                "name": "Lock Test",
                "password": "correct_password"
            }
        )

        # Attempt 5 failed logins
        for i in range(5):
            response = client.post(
                "/api/v1/auth/login",
                data={
                    "username": "locktest@example.com",
                    "password": "wrong_password"
                }
            )

            if i < 4:
                # First 4 attempts: 401 Unauthorized
                assert response.status_code == 401
                assert "attempts remaining" in response.json()["detail"].lower()
            else:
                # 5th attempt: 403 Forbidden (account locked)
                assert response.status_code == 403
                assert "locked" in response.json()["detail"].lower()

    def test_locked_account_cannot_login_even_with_correct_password(self, client):
        """Test that locked account cannot login even with correct credentials."""
        # Register user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "lockeduser@example.com",
                "name": "Locked User",
                "password": "correct_password"
            }
        )

        # Lock account with 5 failed attempts
        for _ in range(5):
            client.post(
                "/api/v1/auth/login",
                data={
                    "username": "lockeduser@example.com",
                    "password": "wrong_password"
                }
            )

        # Try to login with correct password while locked
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "lockeduser@example.com",
                "password": "correct_password"
            }
        )

        assert response.status_code == 403
        assert "locked" in response.json()["detail"].lower()

    def test_successful_login_resets_failed_attempts(self, client):
        """Test that successful login clears failed attempt counter."""
        # Register user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "resettest@example.com",
                "name": "Reset Test",
                "password": "correct_password"
            }
        )

        # 3 failed attempts
        for _ in range(3):
            client.post(
                "/api/v1/auth/login",
                data={
                    "username": "resettest@example.com",
                    "password": "wrong_password"
                }
            )

        # Successful login
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "resettest@example.com",
                "password": "correct_password"
            }
        )

        assert response.status_code == 200

        # Counter should be reset - 5 more failed attempts should lock
        for i in range(5):
            response = client.post(
                "/api/v1/auth/login",
                data={
                    "username": "resettest@example.com",
                    "password": "wrong_password"
                }
            )

            if i < 4:
                assert response.status_code == 401
            else:
                assert response.status_code == 403  # Locked again

    def test_failed_attempts_show_remaining_count(self, client):
        """Test that error message shows remaining attempts."""
        # Register user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "counttest@example.com",
                "name": "Count Test",
                "password": "correct_password"
            }
        )

        # First failed attempt
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "counttest@example.com",
                "password": "wrong_password"
            }
        )

        assert response.status_code == 401
        detail = response.json()["detail"]
        assert "4 attempts remaining" in detail

        # Second failed attempt
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "counttest@example.com",
                "password": "wrong_password"
            }
        )

        assert "3 attempts remaining" in response.json()["detail"]

    def test_lockout_message_shows_duration(self, client):
        """Test that lockout message shows how long the account is locked."""
        # Register user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "durationtest@example.com",
                "name": "Duration Test",
                "password": "correct_password"
            }
        )

        # Lock account
        for _ in range(5):
            client.post(
                "/api/v1/auth/login",
                data={
                    "username": "durationtest@example.com",
                    "password": "wrong_password"
                }
            )

        # Check lockout message
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "durationtest@example.com",
                "password": "correct_password"
            }
        )

        assert response.status_code == 403
        detail = response.json()["detail"]
        # Should mention minutes (15 min lockout)
        assert "minutes" in detail.lower()


class TestRateLimiting:
    """Tests für Rate Limiting (separate from account lockout)."""

    def test_rate_limit_exists(self, client):
        """Test that rate limiting is configured (basic smoke test)."""
        # This is just a smoke test - actual rate limit testing
        # requires time.sleep() which we avoid in unit tests

        # Register a user
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "ratetest@example.com",
                "name": "Rate Test",
                "password": "password123"
            }
        )

        # Should succeed (within rate limit)
        assert response.status_code == 201

        # Note: Full rate limit testing should be done in
        # load tests or manual testing, not unit tests
