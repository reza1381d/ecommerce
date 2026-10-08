"""add currency unit and integer amounts

Revision ID: a75d68e11f34
Revises: 8d3a7b6c1f20
Create Date: 2026-10-08 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "a75d68e11f34"
down_revision = "8d3a7b6c1f20"
branch_labels = None
depends_on = None

MONEY_COLUMNS = {
    "products": ("price",),
    "orders": ("subtotal", "discount_amount", "shipping_amount", "tax_amount", "total_amount"),
    "order_items": ("unit_price", "total_price"),
    "payments": ("amount",),
    "coupons": ("discount_value", "max_discount", "min_order_amount"),
}

def upgrade() -> None:
    op.add_column("store_settings", sa.Column("currency_unit", sa.String(length=10), server_default="toman", nullable=False))
    op.create_check_constraint("ck_store_settings_currency_unit", "store_settings", "currency_unit IN ('toman', 'rial')")
    for table, columns in MONEY_COLUMNS.items():
        for column in columns:
            op.alter_column(table, column, existing_type=sa.Numeric(12, 2), type_=sa.Numeric(12, 0), postgresql_using=f"ROUND({column})")

def downgrade() -> None:
    for table, columns in MONEY_COLUMNS.items():
        for column in columns:
            op.alter_column(table, column, existing_type=sa.Numeric(12, 0), type_=sa.Numeric(12, 2), postgresql_using=f"{column}::numeric(12, 2)")
    op.drop_constraint("ck_store_settings_currency_unit", "store_settings", type_="check")
    op.drop_column("store_settings", "currency_unit")
