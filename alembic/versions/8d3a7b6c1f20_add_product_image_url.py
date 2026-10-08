"""add product image url

Revision ID: 8d3a7b6c1f20
Revises: f2b629bbc181
Create Date: 2026-10-08 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "8d3a7b6c1f20"
down_revision = "f2b629bbc181"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("image_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "image_url")
