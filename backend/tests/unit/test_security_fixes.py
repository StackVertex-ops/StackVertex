"""
Security Quick Fixes - Tests

Tests für alle implementierten Security Fixes.
"""

import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserPasswordUpdate


class TestPasswordComplexity:
    """Test password complexity requirements."""

    def test_weak_password_no_uppercase(self):
        """Weak password - no uppercase."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                name="Test User",
                password="weakpass123!"
            )
        assert "uppercase" in str(exc_info.value).lower()

    def test_weak_password_no_lowercase(self):
        """Weak password - no lowercase."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                name="Test User",
                password="WEAKPASS123!"
            )
        assert "lowercase" in str(exc_info.value).lower()

    def test_weak_password_no_digit(self):
        """Weak password - no digit."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                name="Test User",
                password="WeakPass!!"
            )
        assert "digit" in str(exc_info.value).lower()

    def test_weak_password_no_special_char(self):
        """Weak password - no special character."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                name="Test User",
                password="WeakPass123"
            )
        assert "special" in str(exc_info.value).lower()

    def test_weak_password_too_short(self):
        """Weak password - too short."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                name="Test User",
                password="We1!"
            )
        # Pydantic handles min_length validation
        assert "at least 8" in str(exc_info.value).lower()

    def test_strong_password_accepted(self):
        """Strong password - should be accepted."""
        user = UserCreate(
            email="test@example.com",
            name="Test User",
            password="SecurePass123!"
        )
        assert user.password == "SecurePass123!"

    def test_strong_password_all_special_chars(self):
        """Strong password with various special chars."""
        valid_passwords = [
            "Password1!",
            "Password1@",
            "Password1#",
            "Password1$",
            "Password1%",
            "Password1^",
            "Password1&",
            "Password1*",
            "Password1()",
            "Password1,.",
            "Password1?",
            'Password1"',
            "Password1:",
            "Password1{}",
            "Password1|",
            "Password1<>",
        ]

        for pwd in valid_passwords:
            user = UserCreate(
                email="test@example.com",
                name="Test User",
                password=pwd
            )
            assert user.password == pwd


class TestPasswordUpdateComplexity:
    """Test password complexity for password updates."""

    def test_new_password_weak(self):
        """New password must meet complexity requirements."""
        with pytest.raises(ValidationError) as exc_info:
            UserPasswordUpdate(
                current_password="OldPassword123!",
                new_password="weakpass"
            )
        # Should fail multiple checks
        assert "uppercase" in str(exc_info.value).lower() or "digit" in str(exc_info.value).lower()

    def test_new_password_strong(self):
        """Strong new password should be accepted."""
        update = UserPasswordUpdate(
            current_password="OldPassword123!",
            new_password="NewPassword456!"
        )
        assert update.new_password == "NewPassword456!"


class TestConfigSecurity:
    """Test security config changes."""

    def test_debug_default_false(self):
        """DEBUG should default to False."""
        from app.config import Settings

        # Test that default is False
        # Note: actual value depends on .env, but class default should be False
        settings = Settings(_env_file=None, SECRET_KEY="test-secret-key-minimum-32-characters-long")
        assert settings.DEBUG is False

    def test_access_token_reduced(self):
        """Access token expiry should be 15 minutes (short-lived for security)."""
        from app.config import Settings

        settings = Settings(_env_file=None, SECRET_KEY="test-secret-key-minimum-32-characters-long")
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
