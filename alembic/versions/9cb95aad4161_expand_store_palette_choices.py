"""expand store palette choices

Revision ID: 9cb95aad4161
Revises: e015bebddc85
Create Date: 2026-10-08 01:56:43.848076
"""
from typing import Sequence, Union

from alembic import op


revision: str = "9cb95aad4161"
down_revision: Union[str, Sequence[str], None] = "e015bebddc85"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_PALETTE_CHECK = (
    "palette IN ('blue', 'emerald', 'violet', 'amber', 'rose', "
    "'teal', 'cyan', 'indigo', 'fuchsia', 'lime', 'orange')"
)
OLD_PALETTE_CHECK = "palette IN ('blue', 'emerald', 'violet', 'amber', 'rose')"


def upgrade() -> None:
    op.drop_constraint(
        "ck_store_settings_palette",
        "store_settings",
        type_="check",
    )
    op.create_check_constraint(
        "ck_store_settings_palette",
        "store_settings",
        NEW_PALETTE_CHECK,
    )


def downgrade() -> None:
    op.execute(
        "UPDATE store_settings SET palette = 'blue' "
        "WHERE palette NOT IN ('blue', 'emerald', 'violet', 'amber', 'rose')"
    )
    op.drop_constraint(
        "ck_store_settings_palette",
        "store_settings",
        type_="check",
    )
    op.create_check_constraint(
        "ck_store_settings_palette",
        "store_settings",
        OLD_PALETTE_CHECK,
    )
