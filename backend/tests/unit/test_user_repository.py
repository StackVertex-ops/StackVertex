"""Unit tests für UserRepository.

Fokus: User CRUD, Authentication, Password Hashing, Organisations.
"""

import pytest
from uuid import uuid4
from freezegun import freeze_time

from app.models.user import AuthProvider, UserStatus


class TestUserCreate:
    """Tests für create() method."""

    def test_create_user_with_email_password(self, user_repository):
        """Test creating user with email/password authentication."""
        result = user_repository.create(
            email="alice@example.com",
            name="Alice",
            password="securepassword123"
        )

        assert result["email"] == "alice@example.com"
        assert result["name"] == "Alice"
        assert result["auth_provider"] == AuthProvider.EMAIL.value
        assert result["status"] == UserStatus.ACTIVE.value
        assert "password_hash" in result
        assert result["password_hash"] != "securepassword123"  # Should be hashed
        assert "personal_org_id" in result

    def test_create_user_creates_personal_organisation(self, user_repository, organisation_repository):
        """Test that creating user also creates personal organisation."""
        result = user_repository.create(
            email="bob@example.com",
            name="Bob",
            password="password123"
        )

        # Verify personal org exists
        from uuid import UUID
        personal_org = organisation_repository.get(UUID(result["personal_org_id"]))

        assert personal_org is not None
        assert personal_org["type"] == "personal"
        assert personal_org["owner_user_id"] == result["id"]
        assert "Bob" in personal_org["name"]

    def test_create_user_with_oauth_provider(self, user_repository):
        """Test creating user with OAuth authentication."""
        result = user_repository.create(
            email="charlie@example.com",
            name="Charlie",
            password="dummy",  # Not used for OAuth
            auth_provider=AuthProvider.GOOGLE,
            auth_provider_id="google-oauth-id-123"
        )

        assert result["auth_provider"] == AuthProvider.GOOGLE.value
        assert result["auth_provider_id"] == "google-oauth-id-123"


class TestUserGet:
    """Tests für get() method."""

    def test_get_user_by_id(self, user_repository):
        """Test getting user by UUID."""
        created = user_repository.create(
            email="dave@example.com",
            name="Dave",
            password="password"
        )

        from uuid import UUID
        result = user_repository.get(UUID(created["id"]))

        assert result is not None
        assert result["id"] == created["id"]
        assert result["email"] == "dave@example.com"

    def test_get_nonexistent_user(self, user_repository):
        """Test getting non-existent user returns None."""
        result = user_repository.get(uuid4())

        assert result is None

    def test_get_user_by_email(self, user_repository):
        """Test getting user by email (case-insensitive)."""
        user_repository.create(
            email="Eve@Example.COM",
            name="Eve",
            password="password"
        )

        # Should find with lowercase
        result = user_repository.get_by_email("eve@example.com")

        assert result is not None
        assert result["email"] == "eve@example.com"

    def test_get_user_by_email_case_insensitive(self, user_repository):
        """Test email lookup is case-insensitive."""
        user_repository.create(
            email="frank@example.com",
            name="Frank",
            password="password"
        )

        # Try different case
        result = user_repository.get_by_email("FRANK@EXAMPLE.COM")

        assert result is not None
        assert result["name"] == "Frank"


class TestUserUpdate:
    """Tests für update() method."""

    def test_update_user_name(self, user_repository):
        """Test updating user name."""
        created = user_repository.create(
            email="grace@example.com",
            name="Grace",
            password="password"
        )

        from uuid import UUID
        updated = user_repository.update(
            UUID(created["id"]),
            {"name": "Grace Smith"}
        )

        assert updated["name"] == "Grace Smith"
        assert updated["email"] == created["email"]  # Unchanged

    def test_update_password(self, user_repository):
        """Test updating user password."""
        created = user_repository.create(
            email="henry@example.com",
            name="Henry",
            password="oldpassword"
        )

        from uuid import UUID
        old_hash = created["password_hash"]

        user_repository.update_password(UUID(created["id"]), "newpassword")

        # Get updated user
        updated = user_repository.get(UUID(created["id"]))

        assert updated["password_hash"] != old_hash
        # Verify new password works
        assert user_repository.verify_password("newpassword", updated["password_hash"])

    def test_update_status(self, user_repository):
        """Test updating user status."""
        created = user_repository.create(
            email="iris@example.com",
            name="Iris",
            password="password"
        )

        from uuid import UUID
        updated = user_repository.update_status(
            UUID(created["id"]),
            UserStatus.SUSPENDED
        )

        assert updated["status"] == UserStatus.SUSPENDED.value


class TestUserAuthentication:
    """Tests für authentication methods."""

    def test_verify_password_correct(self, user_repository):
        """Test password verification with correct password."""
        created = user_repository.create(
            email="john@example.com",
            name="John",
            password="correct_password"
        )

        is_valid = user_repository.verify_password(
            "correct_password",
            created["password_hash"]
        )

        assert is_valid is True

    def test_verify_password_incorrect(self, user_repository):
        """Test password verification with wrong password."""
        created = user_repository.create(
            email="kate@example.com",
            name="Kate",
            password="correct_password"
        )

        is_valid = user_repository.verify_password(
            "wrong_password",
            created["password_hash"]
        )

        assert is_valid is False

    def test_authenticate_success(self, user_repository):
        """Test successful authentication."""
        user_repository.create(
            email="leo@example.com",
            name="Leo",
            password="mypassword"
        )

        result = user_repository.authenticate("leo@example.com", "mypassword")

        assert result is not None
        assert result["email"] == "leo@example.com"

    def test_authenticate_wrong_password(self, user_repository):
        """Test authentication fails with wrong password."""
        user_repository.create(
            email="mary@example.com",
            name="Mary",
            password="correct"
        )

        result = user_repository.authenticate("mary@example.com", "wrong")

        assert result is None

    def test_authenticate_nonexistent_user(self, user_repository):
        """Test authentication fails for non-existent user."""
        result = user_repository.authenticate("ghost@example.com", "password")

        assert result is None

    def test_authenticate_inactive_user(self, user_repository):
        """Test authentication fails for inactive user."""
        created = user_repository.create(
            email="nathan@example.com",
            name="Nathan",
            password="password"
        )

        # Set user to inactive
        from uuid import UUID
        user_repository.update_status(UUID(created["id"]), UserStatus.INACTIVE)

        result = user_repository.authenticate("nathan@example.com", "password")

        assert result is None


class TestUserOrganisations:
    """Tests für organisation membership."""

    def test_get_user_organisations(self, user_repository):
        """Test getting user's organisations."""
        created = user_repository.create(
            email="olivia@example.com",
            name="Olivia",
            password="password"
        )

        from uuid import UUID
        orgs = user_repository.get_organisations(UUID(created["id"]))

        # Should have personal org
        assert len(orgs) >= 1
        personal_org = orgs[0]
        assert personal_org["org_id"] == created["personal_org_id"]


class TestUserDelete:
    """Tests für delete() method."""

    def test_delete_user_soft_delete(self, user_repository):
        """Test deleting user (soft delete via status)."""
        created = user_repository.create(
            email="peter@example.com",
            name="Peter",
            password="password"
        )

        from uuid import UUID
        user_id = UUID(created["id"])

        deleted = user_repository.delete(user_id)

        assert deleted is True

        # User still exists but is inactive
        user = user_repository.get(user_id)
        assert user is not None
        assert user["status"] == UserStatus.INACTIVE.value


class TestUserList:
    """Tests für list() method."""

    def test_list_users(self, user_repository):
        """Test listing all users."""
        # Create multiple users
        for i in range(5):
            user_repository.create(
                email=f"user{i}@example.com",
                name=f"User {i}",
                password="password"
            )

        items, total = user_repository.list(skip=0, limit=100)

        assert total >= 5
        assert len(items) >= 5

    def test_list_users_pagination(self, user_repository):
        """Test user list pagination."""
        # Create 10 users
        created_ids = []
        for i in range(10):
            result = user_repository.create(
                email=f"pageuser{i}@example.com",
                name=f"PageUser {i}",
                password="password"
            )
            created_ids.append(result["id"])

        # Get all users we just created
        all_items, total = user_repository.list(skip=0, limit=100)

        # Filter to only our test users
        test_users = [u for u in all_items if u["id"] in created_ids]
        assert len(test_users) == 10

        # First page
        items_page1, _ = user_repository.list(skip=0, limit=3)
        assert len(items_page1) == 3

        # Second page
        items_page2, _ = user_repository.list(skip=3, limit=3)
        assert len(items_page2) == 3

        # Verify different users
        ids_page1 = {item["id"] for item in items_page1}
        ids_page2 = {item["id"] for item in items_page2}
        assert ids_page1.isdisjoint(ids_page2)
