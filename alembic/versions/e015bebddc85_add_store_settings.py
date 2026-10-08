"""add store settings

Revision ID: e015bebddc85
Revises: 37c4f4dc7507
Create Date: 2026-10-07 22:08:51.174886
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e015bebddc85"
down_revision: Union[str, Sequence[str], None] = "37c4f4dc7507"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "store_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("store_name", sa.String(length=60), nullable=False),
        sa.Column("palette", sa.String(length=20), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "palette IN ('blue', 'emerald', 'violet', 'amber', 'rose')",
            name="ck_store_settings_palette",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("store_settings")
