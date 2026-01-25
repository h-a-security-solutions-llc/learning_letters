"""Initial auth tables

Revision ID: 001_initial
Revises:
Create Date: 2026-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime, nullable=True),
    )

    # Create user_settings table
    op.create_table(
        "user_settings",
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("settings_json", sa.Text, nullable=False),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Create user_multiplayer_players table
    op.create_table(
        "user_multiplayer_players",
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("players_json", sa.Text, nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Create user_progress table
    op.create_table(
        "user_progress",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("character", sa.String(1), nullable=False),
        sa.Column("font_name", sa.String(100), nullable=False),
        sa.Column("high_score", sa.Integer, nullable=False),
        sa.Column("stars", sa.Integer, nullable=False),
        sa.Column("attempts_count", sa.Integer, default=1),
        sa.Column("best_attempt_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "character", "font_name", name="uq_user_character_font"),
    )

    # Create refresh_tokens table
    op.create_table(
        "refresh_tokens",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("user_progress")
    op.drop_table("user_multiplayer_players")
    op.drop_table("user_settings")
    op.drop_table("users")
