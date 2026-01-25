"""Progress router for tracking high scores per character."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.progress import UserProgress
from app.models.user import User

router = APIRouter(prefix="/progress", tags=["progress"])


# Request/Response models
class ProgressResponse(BaseModel):
    """Single progress entry response."""

    id: str
    character: str
    font_name: str
    mode: str  # freestyle, tracing, step-by-step
    high_score: int
    stars: int
    attempts_count: int
    best_attempt_at: datetime


class AllProgressResponse(BaseModel):
    """All progress entries response."""

    progress: List[ProgressResponse]


class RecordAttemptRequest(BaseModel):
    """Record a new attempt request."""

    font_name: str
    mode: str = "freestyle"  # freestyle, tracing, step-by-step
    score: int
    stars: int


class RecordAttemptResponse(BaseModel):
    """Response after recording an attempt."""

    is_new_high_score: bool
    previous_high_score: Optional[int]
    current_high_score: int
    progress: ProgressResponse


@router.get("/", response_model=AllProgressResponse)
async def get_all_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all progress entries for the current user.

    Returns high scores for all characters the user has practiced.
    """
    result = await db.execute(
        select(UserProgress).where(UserProgress.user_id == current_user.id).order_by(UserProgress.character)
    )
    progress_list = result.scalars().all()

    return AllProgressResponse(
        progress=[
            ProgressResponse(
                id=p.id,
                character=p.character,
                font_name=p.font_name,
                mode=p.mode,
                high_score=p.high_score,
                stars=p.stars,
                attempts_count=p.attempts_count,
                best_attempt_at=p.best_attempt_at,
            )
            for p in progress_list
        ]
    )


@router.get("/{character}", response_model=ProgressResponse)
async def get_character_progress(
    character: str,
    font_name: Optional[str] = None,
    mode: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get progress for a specific character.

    - font_name: Filter by font (optional)
    - mode: Filter by mode - freestyle, tracing, step-by-step (optional)
    Returns the best progress matching the filters.
    """
    if len(character) != 1:
        raise HTTPException(status_code=400, detail="Character must be a single character")

    query = select(UserProgress).where(
        UserProgress.user_id == current_user.id,
        UserProgress.character == character,
    )

    if font_name:
        query = query.where(UserProgress.font_name == font_name)
    if mode:
        query = query.where(UserProgress.mode == mode)

    # Get the best score matching filters
    query = query.order_by(UserProgress.high_score.desc())

    result = await db.execute(query)
    progress = result.scalar_one_or_none()

    if progress is None:
        raise HTTPException(status_code=404, detail="No progress found for this character")

    return ProgressResponse(
        id=progress.id,
        character=progress.character,
        font_name=progress.font_name,
        mode=progress.mode,
        high_score=progress.high_score,
        stars=progress.stars,
        attempts_count=progress.attempts_count,
        best_attempt_at=progress.best_attempt_at,
    )


@router.post("/{character}", response_model=RecordAttemptResponse)
async def record_attempt(
    character: str,
    request: RecordAttemptRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Record a practice attempt for a character.

    Updates the high score if the new score is better.
    Always increments the attempts counter.
    """
    if len(character) != 1:
        raise HTTPException(status_code=400, detail="Character must be a single character")

    if not request.font_name:
        raise HTTPException(status_code=400, detail="Font name is required")

    if request.stars < 0 or request.stars > 5:
        raise HTTPException(status_code=400, detail="Stars must be between 0 and 5")

    # Validate mode
    valid_modes = ["freestyle", "tracing", "step-by-step"]
    mode = request.mode if request.mode in valid_modes else "freestyle"

    # Find existing progress for this character/font/mode
    result = await db.execute(
        select(UserProgress).where(
            UserProgress.user_id == current_user.id,
            UserProgress.character == character,
            UserProgress.font_name == request.font_name,
            UserProgress.mode == mode,
        )
    )
    progress = result.scalar_one_or_none()

    previous_high_score = None
    is_new_high_score = False

    if progress is None:
        # Create new progress entry
        progress = UserProgress(
            user_id=current_user.id,
            character=character,
            font_name=request.font_name,
            mode=mode,
            high_score=request.score,
            stars=request.stars,
            attempts_count=1,
            best_attempt_at=datetime.utcnow(),
        )
        db.add(progress)
        is_new_high_score = True
    else:
        # Update existing progress
        previous_high_score = progress.high_score
        progress.attempts_count += 1

        if request.score > progress.high_score:
            progress.high_score = request.score
            progress.stars = request.stars
            progress.best_attempt_at = datetime.utcnow()
            is_new_high_score = True

    await db.flush()

    return RecordAttemptResponse(
        is_new_high_score=is_new_high_score,
        previous_high_score=previous_high_score,
        current_high_score=progress.high_score,
        progress=ProgressResponse(
            id=progress.id,
            character=progress.character,
            font_name=progress.font_name,
            mode=progress.mode,
            high_score=progress.high_score,
            stars=progress.stars,
            attempts_count=progress.attempts_count,
            best_attempt_at=progress.best_attempt_at,
        ),
    )


class ClearProgressRequest(BaseModel):
    """Request to clear progress for specific modes."""

    modes: List[str]  # List of modes to clear: freestyle, tracing, step-by-step


class ClearProgressResponse(BaseModel):
    """Response after clearing progress."""

    deleted_count: int


@router.delete("/", response_model=ClearProgressResponse)
async def clear_progress(
    request: ClearProgressRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Clear progress for the current user for specified modes.

    - **modes**: List of modes to clear (freestyle, tracing, step-by-step)
    """
    valid_modes = ["freestyle", "tracing", "step-by-step"]
    modes_to_clear = [m for m in request.modes if m in valid_modes]

    if not modes_to_clear:
        raise HTTPException(status_code=400, detail="No valid modes specified")

    # Delete progress entries for the specified modes
    result = await db.execute(
        delete(UserProgress).where(
            UserProgress.user_id == current_user.id,
            UserProgress.mode.in_(modes_to_clear),
        )
    )

    deleted_count = result.rowcount

    return ClearProgressResponse(deleted_count=deleted_count)
