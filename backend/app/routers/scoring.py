"""Scoring router for evaluating drawn characters."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user_optional
from app.models.progress import UserProgress
from app.models.user import User
from app.services.scoring import score_drawing

router = APIRouter()


class ScoreRequest(BaseModel):
    """Request model for scoring a drawn character."""

    image_data: str  # Base64 encoded image
    character: str  # The character that was drawn
    font: Optional[str] = None  # Font name (e.g., 'Fredoka-Regular')
    mode: str = "freestyle"  # Drawing mode: freestyle, tracing, step-by-step
    record_progress: bool = True  # Whether to record progress (when logged in)


class ScoreResponse(BaseModel):
    """Response model for character scoring."""

    score: int
    stars: int
    feedback: str
    details: dict
    reference_image: str
    debug: Optional[dict] = None
    is_new_high_score: Optional[bool] = None  # Only set when logged in
    previous_high_score: Optional[int] = None  # Only set when logged in
    high_score_for_mode: Optional[int] = None  # Current high score for this mode


@router.post("/score", response_model=ScoreResponse)
async def score_character(
    request: ScoreRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Score a drawn character against the reference.

    - **image_data**: Base64 encoded PNG image of the drawing
    - **character**: The character that was supposed to be drawn (e.g., 'A', 'a', '5')
    - **font**: Optional font name
    - **record_progress**: Whether to record progress (when logged in)
    """
    if not request.image_data:
        raise HTTPException(status_code=400, detail="Image data is required")

    if not request.character or len(request.character) != 1:
        raise HTTPException(status_code=400, detail="Single character is required")

    result = score_drawing(request.image_data, request.character, request.font)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # Validate mode
    valid_modes = ["freestyle", "tracing", "step-by-step"]
    mode = request.mode if request.mode in valid_modes else "freestyle"

    # Record progress if user is logged in and record_progress is True
    is_new_high_score = None
    previous_high_score = None
    high_score_for_mode = None

    if current_user and request.record_progress and request.font:
        # Find existing progress for this character/font/mode
        query_result = await db.execute(
            select(UserProgress).where(
                UserProgress.user_id == current_user.id,
                UserProgress.character == request.character,
                UserProgress.font_name == request.font,
                UserProgress.mode == mode,
            )
        )
        progress = query_result.scalar_one_or_none()

        score = result["score"]
        stars = result["stars"]

        if progress is None:
            # Create new progress entry
            progress = UserProgress(
                user_id=current_user.id,
                character=request.character,
                font_name=request.font,
                mode=mode,
                high_score=score,
                stars=stars,
                attempts_count=1,
                best_attempt_at=datetime.utcnow(),
            )
            db.add(progress)
            is_new_high_score = True
            high_score_for_mode = score
        else:
            # Update existing progress
            previous_high_score = progress.high_score
            high_score_for_mode = progress.high_score
            progress.attempts_count += 1

            if score > progress.high_score:
                progress.high_score = score
                progress.stars = stars
                progress.best_attempt_at = datetime.utcnow()
                is_new_high_score = True
                high_score_for_mode = score
            else:
                is_new_high_score = False

    return ScoreResponse(
        score=result["score"],
        stars=result["stars"],
        feedback=result["feedback"],
        details=result["details"],
        reference_image=result["reference_image"],
        debug=result.get("debug"),
        is_new_high_score=is_new_high_score,
        previous_high_score=previous_high_score,
        high_score_for_mode=high_score_for_mode,
    )
