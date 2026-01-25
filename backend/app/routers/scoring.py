"""Scoring router for evaluating drawn characters."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.scoring import score_drawing

router = APIRouter()


class ScoreRequest(BaseModel):
    """Request model for scoring a drawn character."""

    image_data: str  # Base64 encoded image
    character: str  # The character that was drawn
    font: Optional[str] = None  # Font name (e.g., 'Fredoka-Regular')


class ScoreResponse(BaseModel):
    """Response model for character scoring."""

    score: int
    stars: int
    feedback: str
    details: dict
    reference_image: str
    debug: Optional[dict] = None


@router.post("/score", response_model=ScoreResponse)
async def score_character(request: ScoreRequest):
    """
    Score a drawn character against the reference.

    - **image_data**: Base64 encoded PNG image of the drawing
    - **character**: The character that was supposed to be drawn (e.g., 'A', 'a', '5')
    """
    if not request.image_data:
        raise HTTPException(status_code=400, detail="Image data is required")

    if not request.character or len(request.character) != 1:
        raise HTTPException(status_code=400, detail="Single character is required")

    result = score_drawing(request.image_data, request.character, request.font)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result
