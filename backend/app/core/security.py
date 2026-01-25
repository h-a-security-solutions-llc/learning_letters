"""Security utilities for JWT tokens and password hashing."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import get_settings

settings = get_settings()

# Argon2id password hasher (recommended for password hashing)
# - No password length limits
# - Memory-hard (resists GPU attacks)
# - Winner of the Password Hashing Competition
ph = PasswordHasher()


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str  # User ID
    exp: datetime
    type: str  # "access" or "refresh"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return ph.hash(password)


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token() -> str:
    """Create a random refresh token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a token for storage (using SHA-256)."""
    return hashlib.sha256(token.encode()).hexdigest()


def decode_access_token(token: str) -> Optional[TokenPayload]:
    """Decode and validate an access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "access":
            return None
        return TokenPayload(**payload)
    except JWTError:
        return None


def get_refresh_token_expires() -> datetime:
    """Get the expiration datetime for a refresh token."""
    return datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    Returns (is_valid, error_message).
    Password must be 8-50 characters with uppercase, lowercase, and a number.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if len(password) > 50:
        return False, "Password must be at most 50 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """
    Basic email validation.
    Returns (is_valid, error_message).
    """
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return False, "Invalid email format"
    if len(email) > 255:
        return False, "Email address is too long"
    return True, ""
