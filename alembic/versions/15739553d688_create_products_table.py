"""create products table

Revision ID: 15739553d688
Revises: 7af5e55bee0c
Create Date: 2026-09-15 00:40:56.249099

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "15739553d688"
down_revision: Union[str, Sequence[str], None] = "7af5e55bee0c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "products",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "price",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),
        sa.Column(
            "stock",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "reserved_stock",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "category_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "price >= 0",
            name="ck_products_price_non_negative",
        ),
        sa.CheckConstraint(
            "stock >= 0",
            name="ck_products_stock_non_negative",
        ),
        sa.CheckConstraint(
            "reserved_stock >= 0",
            name="ck_products_reserved_stock_non_negative",
        ),
        sa.CheckConstraint(
            "reserved_stock <= stock",
            name="ck_products_reserved_stock_lte_stock",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("products")