"""User settings router for syncing settings and multiplayer players."""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.settings import UserMultiplayerPlayers, UserSettings
from app.models.user import User

router = APIRouter(prefix="/user", tags=["user"])


# Request/Response models
class SettingsResponse(BaseModel):
    """User settings response."""

    settings: dict
    version: int
    updated_at: datetime


class UpdateSettingsRequest(BaseModel):
    """Update settings request."""

    settings: dict
    version: Optional[int] = None  # For optimistic locking


class MergeSettingsRequest(BaseModel):
    """Merge local settings request (first login)."""

    local_settings: dict


class MultiplayerPlayersResponse(BaseModel):
    """Multiplayer players response."""

    players: list
    updated_at: datetime


class UpdateMultiplayerPlayersRequest(BaseModel):
    """Update multiplayer players request."""

    players: list


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user settings.

    Returns the user's saved settings or empty settings if none exist.
    """
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    user_settings = result.scalar_one_or_none()

    if user_settings is None:
        # Return empty settings for new users
        return SettingsResponse(
            settings={},
            version=0,
            updated_at=datetime.utcnow(),
        )

    return SettingsResponse(
        settings=json.loads(user_settings.settings_json),
        version=user_settings.version,
        updated_at=user_settings.updated_at,
    )


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(
    request: UpdateSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user settings.

    If version is provided, only updates if the server version matches (optimistic locking).
    Returns 409 Conflict if versions don't match.
    """
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    user_settings = result.scalar_one_or_none()

    if user_settings is None:
        # Create new settings
        user_settings = UserSettings(
            user_id=current_user.id,
            settings_json=json.dumps(request.settings),
            version=1,
        )
        db.add(user_settings)
    else:
        # Check version for optimistic locking
        if request.version is not None and request.version != user_settings.version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Settings have been modified. Please refresh and try again.",
            )

        # Update existing settings
        user_settings.settings_json = json.dumps(request.settings)
        user_settings.version += 1
        user_settings.updated_at = datetime.utcnow()

    await db.flush()

    return SettingsResponse(
        settings=json.loads(user_settings.settings_json),
        version=user_settings.version,
        updated_at=user_settings.updated_at,
    )


@router.post("/settings/merge", response_model=SettingsResponse)
async def merge_settings(
    request: MergeSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Merge local settings with server settings.

    Used on first login to merge localStorage data with any existing server settings.
    Local settings take precedence for conflicts.
    """
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    user_settings = result.scalar_one_or_none()

    if user_settings is None:
        # No existing settings - just save local settings
        user_settings = UserSettings(
            user_id=current_user.id,
            settings_json=json.dumps(request.local_settings),
            version=1,
        )
        db.add(user_settings)
    else:
        # Merge: server settings as base, local settings override
        server_settings = json.loads(user_settings.settings_json)
        merged_settings = {**server_settings, **request.local_settings}
        user_settings.settings_json = json.dumps(merged_settings)
        user_settings.version += 1
        user_settings.updated_at = datetime.utcnow()

    await db.flush()

    return SettingsResponse(
        settings=json.loads(user_settings.settings_json),
        version=user_settings.version,
        updated_at=user_settings.updated_at,
    )


@router.get("/multiplayer-players", response_model=MultiplayerPlayersResponse)
async def get_multiplayer_players(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get saved multiplayer player configurations.
    """
    result = await db.execute(select(UserMultiplayerPlayers).where(UserMultiplayerPlayers.user_id == current_user.id))
    players_record = result.scalar_one_or_none()

    if players_record is None:
        return MultiplayerPlayersResponse(
            players=[],
            updated_at=datetime.utcnow(),
        )

    return MultiplayerPlayersResponse(
        players=json.loads(players_record.players_json),
        updated_at=players_record.updated_at,
    )


@router.put("/multiplayer-players", response_model=MultiplayerPlayersResponse)
async def update_multiplayer_players(
    request: UpdateMultiplayerPlayersRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update multiplayer player configurations.
    """
    result = await db.execute(select(UserMultiplayerPlayers).where(UserMultiplayerPlayers.user_id == current_user.id))
    players_record = result.scalar_one_or_none()

    if players_record is None:
        players_record = UserMultiplayerPlayers(
            user_id=current_user.id,
            players_json=json.dumps(request.players),
        )
        db.add(players_record)
    else:
        players_record.players_json = json.dumps(request.players)
        players_record.updated_at = datetime.utcnow()

    await db.flush()

    return MultiplayerPlayersResponse(
        players=json.loads(players_record.players_json),
        updated_at=players_record.updated_at,
    )
