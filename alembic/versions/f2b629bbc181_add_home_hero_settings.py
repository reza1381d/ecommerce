"""add home hero settings

Revision ID: f2b629bbc181
Revises: 9cb95aad4161
Create Date: 2026-10-08 02:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2b629bbc181"
down_revision: Union[str, Sequence[str], None] = "9cb95aad4161"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "store_settings",
        sa.Column("home_hero_badge", sa.String(length=80), nullable=True),
    )
    op.add_column(
        "store_settings",
        sa.Column("home_hero_title", sa.String(length=160), nullable=True),
    )
    op.add_column(
        "store_settings",
        sa.Column("home_hero_description", sa.Text(), nullable=True),
    )
    op.add_column(
        "store_settings",
        sa.Column("home_hero_button_label", sa.String(length=50), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE store_settings SET "
            "home_hero_badge = store_name, "
            "home_hero_title = :title, "
            "home_hero_description = :description, "
            "home_hero_button_label = :button_label"
        ).bindparams(
            title="خریدی ساده،\nانتخابی مطمئن",
            description="محصولات فروشگاه را ببینید، جست‌وجو کنید و گزینه‌ی مناسب خودتان را پیدا کنید.",
            button_label="مشاهده محصولات",
        )
    )
    op.alter_column("store_settings", "home_hero_badge", nullable=False)
    op.alter_column("store_settings", "home_hero_title", nullable=False)
    op.alter_column("store_settings", "home_hero_description", nullable=False)
    op.alter_column("store_settings", "home_hero_button_label", nullable=False)


def downgrade() -> None:
    op.drop_column("store_settings", "home_hero_button_label")
    op.drop_column("store_settings", "home_hero_description")
    op.drop_column("store_settings", "home_hero_title")
    op.drop_column("store_settings", "home_hero_badge")
