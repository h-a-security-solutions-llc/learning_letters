"""User settings and multiplayer players models."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserSettings(Base):
    """User settings stored as JSON blob."""

    __tablename__ = "user_settings"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    settings_json: Mapped[str] = mapped_column(Text, nullable=False)  # Full AppSettings object
    version: Mapped[int] = mapped_column(Integer, default=1)  # For conflict resolution
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="settings")

    def __repr__(self) -> str:
        return f"<UserSettings(user_id={self.user_id}, version={self.version})>"


class UserMultiplayerPlayers(Base):
    """Multiplayer player configurations."""

    __tablename__ = "user_multiplayer_players"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    players_json: Mapped[str] = mapped_column(Text, nullable=False)  # Array of player configs
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="multiplayer_players")

    def __repr__(self) -> str:
        return f"<UserMultiplayerPlayers(user_id={self.user_id})>"
