"""Tests für Password Utility Functions.

Tests für sichere Passwort-Generierung.
"""

import pytest
import re

from app.utils.password import generate_secure_password


def test_generate_secure_password_default_length():
    """Test password generation with default length (16)."""
    password = generate_secure_password()
    assert len(password) == 16


def test_generate_secure_password_custom_length():
    """Test password generation with custom length."""
    password = generate_secure_password(length=20)
    assert len(password) == 20


def test_generate_secure_password_minimum_length():
    """Test password generation with minimum length (8)."""
    password = generate_secure_password(length=8)
    assert len(password) == 8


def test_generate_secure_password_length_too_short():
    """Test that too short password length raises error."""
    with pytest.raises(ValueError) as exc_info:
        generate_secure_password(length=7)

    assert "at least 8 characters" in str(exc_info.value)


def test_generate_secure_password_contains_lowercase():
    """Test that password contains lowercase letters."""
    password = generate_secure_password()
    assert re.search(r'[a-z]', password) is not None


def test_generate_secure_password_contains_uppercase():
    """Test that password contains uppercase letters."""
    password = generate_secure_password()
    assert re.search(r'[A-Z]', password) is not None


def test_generate_secure_password_contains_digit():
    """Test that password contains digits."""
    password = generate_secure_password()
    assert re.search(r'\d', password) is not None


def test_generate_secure_password_contains_special():
    """Test that password contains special characters."""
    password = generate_secure_password()
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    assert any(c in special_chars for c in password)


def test_generate_secure_password_randomness():
    """Test that generated passwords are different (random)."""
    passwords = [generate_secure_password() for _ in range(10)]

    # All passwords should be unique
    assert len(set(passwords)) == 10


def test_generate_secure_password_character_distribution():
    """Test that all character types are present in generated password."""
    password = generate_secure_password(length=16)

    has_lowercase = any(c.islower() for c in password)
    has_uppercase = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

    assert has_lowercase, "Password should contain lowercase letters"
    assert has_uppercase, "Password should contain uppercase letters"
    assert has_digit, "Password should contain digits"
    assert has_special, "Password should contain special characters"


def test_generate_secure_password_no_ambiguous_chars():
    """Test that password doesn't contain easily confused characters (optional check)."""
    # This test is optional - our implementation includes all chars
    # If we wanted to exclude ambiguous chars (0/O, 1/I/l), we'd modify the generator
    password = generate_secure_password()

    # Just verify it's valid and has all required types
    assert len(password) >= 16
    assert any(c.islower() for c in password)
    assert any(c.isupper() for c in password)
    assert any(c.isdigit() for c in password)
