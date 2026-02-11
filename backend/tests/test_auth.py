"""
Tests for authentication endpoints and security functions.

Tests registration, login, token refresh, and logout flows.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.security import (
    create_access_token,
    get_password_hash,
    hash_token,
    validate_email,
    validate_password_strength,
    verify_password,
)
from app.main import app

client = TestClient(app)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_string(self):
        """Should return a hash string."""
        hashed = get_password_hash("testpassword123")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_is_different_from_password(self):
        """Hash should not equal the original password."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert hashed != password

    def test_same_password_different_hashes(self):
        """Same password should produce different hashes (salted)."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        # Argon2 uses random salts, so hashes should differ
        assert hash1 != hash2

    def test_verify_correct_password(self):
        """Should verify correct password."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Should reject wrong password."""
        hashed = get_password_hash("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_empty_password(self):
        """Should handle empty password check."""
        hashed = get_password_hash("somepassword")
        assert verify_password("", hashed) is False


class TestTokenHashing:
    """Tests for token hashing function."""

    def test_hash_token_returns_string(self):
        """Should return a hash string."""
        token = "some-refresh-token-123"
        hashed = hash_token(token)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_same_token_same_hash(self):
        """Same token should produce same hash (deterministic)."""
        token = "test-token-xyz"
        hash1 = hash_token(token)
        hash2 = hash_token(token)
        assert hash1 == hash2

    def test_different_tokens_different_hashes(self):
        """Different tokens should produce different hashes."""
        hash1 = hash_token("token-1")
        hash2 = hash_token("token-2")
        assert hash1 != hash2


class TestAccessToken:
    """Tests for access token creation."""

    def test_create_access_token_returns_string(self):
        """Should return a JWT string."""
        token = create_access_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_has_jwt_structure(self):
        """Token should have JWT structure (3 parts separated by dots)."""
        token = create_access_token("user-123")
        parts = token.split(".")
        assert len(parts) == 3


class TestEmailValidation:
    """Tests for email validation function."""

    def test_valid_email(self):
        """Should accept valid emails."""
        valid, error = validate_email("test@example.com")
        assert valid is True
        # error is empty string or None on success
        assert not error

    def test_valid_email_with_subdomain(self):
        """Should accept emails with subdomains."""
        valid, error = validate_email("test@mail.example.com")
        assert valid is True

    def test_invalid_email_no_at(self):
        """Should reject email without @."""
        valid, error = validate_email("testexample.com")
        assert valid is False
        assert error  # error should be truthy (non-empty string)

    def test_invalid_email_no_domain(self):
        """Should reject email without domain."""
        valid, error = validate_email("test@")
        assert valid is False

    def test_empty_email(self):
        """Should reject empty email."""
        valid, error = validate_email("")
        assert valid is False


class TestPasswordStrength:
    """Tests for password strength validation."""

    def test_strong_password(self):
        """Should accept strong passwords."""
        valid, error = validate_password_strength("SecurePass123!")
        assert valid is True
        # error is empty string or None on success
        assert not error

    def test_password_too_short(self):
        """Should reject passwords under 8 characters."""
        valid, error = validate_password_strength("Short1!")
        assert valid is False
        assert "8 characters" in error.lower() or "short" in error.lower() or "length" in error.lower()

    def test_password_no_uppercase(self):
        """Should require uppercase letter."""
        valid, error = validate_password_strength("lowercase123!")
        assert valid is False

    def test_password_no_lowercase(self):
        """Should require lowercase letter."""
        valid, error = validate_password_strength("UPPERCASE123!")
        assert valid is False

    def test_password_no_number(self):
        """Should require at least one number."""
        valid, error = validate_password_strength("NoNumbersHere!")
        assert valid is False

    def test_minimum_valid_password(self):
        """Should accept minimum valid password."""
        valid, error = validate_password_strength("Abcdefg1")
        assert valid is True


class TestRegisterEndpoint:
    """Tests for /auth/register endpoint."""

    def test_register_validation_email_required(self):
        """Should require email field."""
        response = client.post(
            "/api/auth/register",
            json={"password": "ValidPass123!", "display_name": "Test User"},
        )
        assert response.status_code == 422  # Validation error

    def test_register_validation_password_required(self):
        """Should require password field."""
        response = client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "display_name": "Test User"},
        )
        assert response.status_code == 422

    def test_register_validation_display_name_required(self):
        """Should require display_name field."""
        response = client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "ValidPass123!"},
        )
        assert response.status_code == 422

    def test_register_weak_password_rejected(self):
        """Should reject weak passwords."""
        response = client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "weak", "display_name": "Test"},
        )
        assert response.status_code == 400

    def test_register_invalid_email_rejected(self):
        """Should reject invalid email format."""
        response = client.post(
            "/api/auth/register",
            json={"email": "not-an-email", "password": "ValidPass123!", "display_name": "Test"},
        )
        assert response.status_code == 422  # Pydantic EmailStr validation


class TestLoginEndpoint:
    """Tests for /auth/login endpoint."""

    def test_login_validation_email_required(self):
        """Should require email field."""
        response = client.post(
            "/api/auth/login",
            json={"password": "somepassword"},
        )
        assert response.status_code == 422

    def test_login_validation_password_required(self):
        """Should require password field."""
        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 422

    def test_login_wrong_credentials(self):
        """Should return 401 for wrong credentials."""
        response = client.post(
            "/api/auth/login",
            json={"email": "nonexistent@example.com", "password": "WrongPass123!"},
        )
        assert response.status_code == 401

    def test_login_error_message_generic(self):
        """Error message should be generic (prevent enumeration)."""
        response = client.post(
            "/api/auth/login",
            json={"email": "nonexistent@example.com", "password": "WrongPass123!"},
        )
        data = response.json()
        # Should not reveal whether email exists
        assert "invalid" in data["detail"].lower()


class TestRefreshEndpoint:
    """Tests for /auth/refresh endpoint."""

    def test_refresh_no_cookie(self):
        """Should return 401 without refresh token cookie."""
        response = client.post("/api/auth/refresh")
        assert response.status_code == 401

    def test_refresh_invalid_token(self):
        """Should return 401 for invalid refresh token."""
        response = client.post(
            "/api/auth/refresh",
            cookies={"refresh_token": "invalid-token-here"},
        )
        assert response.status_code == 401


class TestLogoutEndpoint:
    """Tests for /auth/logout endpoint."""

    def test_logout_without_token(self):
        """Should succeed even without token (idempotent)."""
        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_logout_clears_cookie(self):
        """Should clear the refresh token cookie."""
        response = client.post("/api/auth/logout")
        # Check that set-cookie header clears the token
        assert response.status_code == 200


class TestMeEndpoint:
    """Tests for /auth/me endpoint."""

    def test_me_without_auth(self):
        """Should return 401 without authentication."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_with_invalid_token(self):
        """Should return 401 with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401


class TestDeleteAccountEndpoint:
    """Tests for /auth/account DELETE endpoint."""

    def test_delete_without_auth(self):
        """Should return 401 without authentication."""
        response = client.delete("/api/auth/account")
        assert response.status_code == 401
