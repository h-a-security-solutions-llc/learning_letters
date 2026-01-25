"""User progress model for tracking high scores per character."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserProgress(Base):
    """High scores per character for a user."""

    __tablename__ = "user_progress"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    character: Mapped[str] = mapped_column(String(1), nullable=False)  # 'A', 'a', '1', etc.
    font_name: Mapped[str] = mapped_column(String(100), nullable=False)
    mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="freestyle"
    )  # freestyle, tracing, step-by-step
    high_score: Mapped[int] = mapped_column(Integer, nullable=False)
    stars: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5 stars
    attempts_count: Mapped[int] = mapped_column(Integer, default=1)
    best_attempt_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Unique constraint for user + character + font + mode combination
    __table_args__ = (
        UniqueConstraint("user_id", "character", "font_name", "mode", name="uq_user_character_font_mode"),
    )

    # Relationship
    user = relationship("User", back_populates="progress")

    def __repr__(self) -> str:
        return f"<UserProgress(user_id={self.user_id}, character={self.character}, high_score={self.high_score})>"
