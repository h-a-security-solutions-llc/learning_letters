"""Authentication router for user registration, login, and token management."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    get_refresh_token_expires,
    hash_token,
    validate_email,
    validate_password_strength,
    verify_password,
)
from app.deps import get_current_user, get_refresh_token_from_cookie
from app.models.refresh_token import RefreshToken
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


# Request/Response models
class RegisterRequest(BaseModel):
    """Registration request."""

    email: EmailStr
    password: str
    display_name: str


class LoginRequest(BaseModel):
    """Login request."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response for login/register."""

    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    """User data response."""

    model_config = {"from_attributes": True}

    id: str
    email: str
    display_name: str
    created_at: datetime


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


# Utility to set refresh token cookie
def set_refresh_token_cookie(response: Response, token: str) -> None:
    """Set the refresh token as an httpOnly cookie."""
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=True,  # Only send over HTTPS in production
        samesite="lax",
        max_age=30 * 24 * 60 * 60,  # 30 days in seconds
        path="/api/auth",  # Only send to auth endpoints
    )


def clear_refresh_token_cookie(response: Response) -> None:
    """Clear the refresh token cookie."""
    response.delete_cookie(
        key="refresh_token",
        path="/api/auth",
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user account.

    - **email**: User's email address (must be unique)
    - **password**: Password (min 8 chars, mixed case, at least one number)
    - **display_name**: Display name shown in the app
    """
    # Validate email
    email_valid, email_error = validate_email(request.email)
    if not email_valid:
        raise HTTPException(status_code=400, detail=email_error)

    # Validate password strength
    password_valid, password_error = validate_password_strength(request.password)
    if not password_valid:
        raise HTTPException(status_code=400, detail=password_error)

    # Validate display name
    if not request.display_name or len(request.display_name.strip()) < 1:
        raise HTTPException(status_code=400, detail="Display name is required")
    if len(request.display_name) > 100:
        raise HTTPException(status_code=400, detail="Display name is too long")

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == request.email.lower()))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = User(
        email=request.email.lower(),
        display_name=request.display_name.strip(),
        password_hash=get_password_hash(request.password),
        last_login_at=datetime.utcnow(),
    )
    db.add(user)
    await db.flush()  # Get the user ID

    # Create tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token()

    # Store refresh token hash
    token_record = RefreshToken(
        token_hash=hash_token(refresh_token),
        user_id=user.id,
        expires_at=get_refresh_token_expires(),
    )
    db.add(token_record)

    # Set refresh token cookie
    set_refresh_token_cookie(response, refresh_token)

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with email and password.

    Returns JWT access token and sets refresh token cookie.
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == request.email.lower()))
    user = result.scalar_one_or_none()

    # Generic error message to prevent email enumeration
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Update last login
    user.last_login_at = datetime.utcnow()

    # Create tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token()

    # Store refresh token hash
    token_record = RefreshToken(
        token_hash=hash_token(refresh_token),
        user_id=user.id,
        expires_at=get_refresh_token_expires(),
    )
    db.add(token_record)

    # Set refresh token cookie
    set_refresh_token_cookie(response, refresh_token)

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    token: Optional[str] = Depends(get_refresh_token_from_cookie),
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token from cookie.

    Implements token rotation - old token is invalidated and new one issued.
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided",
        )

    # Find token by hash
    token_hash = hash_token(token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    token_record = result.scalar_one_or_none()

    if token_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if token_record.is_expired:
        # Delete expired token
        await db.delete(token_record)
        clear_refresh_token_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Get user
    user_result = await db.execute(select(User).where(User.id == token_record.user_id))
    user: Optional[User] = user_result.scalar_one_or_none()

    if user is None:
        await db.delete(token_record)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Token rotation: delete old token, create new one
    await db.delete(token_record)

    access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token()

    new_token_record = RefreshToken(
        token_hash=hash_token(new_refresh_token),
        user_id=user.id,
        expires_at=get_refresh_token_expires(),
    )
    db.add(new_token_record)

    # Set new refresh token cookie
    set_refresh_token_cookie(response, new_refresh_token)

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    token: Optional[str] = Depends(get_refresh_token_from_cookie),
    db: AsyncSession = Depends(get_db),
):
    """
    Logout user by revoking refresh token.

    Clears the refresh token cookie.
    """
    if token:
        # Delete token from database
        token_hash = hash_token(token)
        result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        token_record = result.scalar_one_or_none()
        if token_record:
            await db.delete(token_record)

    # Clear cookie
    clear_refresh_token_cookie(response)

    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    Get current user profile.

    Requires valid access token.
    """
    return UserResponse.model_validate(current_user)


@router.delete("/account", response_model=MessageResponse)
async def delete_account(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete user account (GDPR compliance).

    This permanently deletes the user and all associated data.
    """
    await db.delete(current_user)
    clear_refresh_token_cookie(response)

    return MessageResponse(message="Account deleted successfully")
