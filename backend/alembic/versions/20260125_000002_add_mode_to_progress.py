"""Add mode column to user_progress

Revision ID: 002_add_mode
Revises: 001_initial
Create Date: 2026-01-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_add_mode"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("user_progress") as batch_op:
        # Add mode column with default value
        batch_op.add_column(
            sa.Column("mode", sa.String(20), nullable=False, server_default="freestyle"),
        )
        # Drop old unique constraint and create new one including mode
        batch_op.drop_constraint("uq_user_character_font", type_="unique")
        batch_op.create_unique_constraint(
            "uq_user_character_font_mode",
            ["user_id", "character", "font_name", "mode"],
        )


def downgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("user_progress") as batch_op:
        # Drop new constraint and recreate old one
        batch_op.drop_constraint("uq_user_character_font_mode", type_="unique")
        batch_op.create_unique_constraint(
            "uq_user_character_font",
            ["user_id", "character", "font_name"],
        )
        # Remove mode column
        batch_op.drop_column("mode")
