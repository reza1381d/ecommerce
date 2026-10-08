from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StoreSetting(Base):
    __tablename__ = "store_settings"

    __table_args__ = (
        CheckConstraint(
            "palette IN ('blue', 'emerald', 'violet', 'amber', 'rose', 'teal', 'cyan', 'indigo', 'fuchsia', 'lime', 'orange')",
            name="ck_store_settings_palette",
        ),
        CheckConstraint("currency_unit IN ('toman', 'rial')", name="ck_store_settings_currency_unit"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store_name: Mapped[str] = mapped_column(
        String(60), nullable=False, default="فروشگاه اینترنتی"
    )
    palette: Mapped[str] = mapped_column(String(20), nullable=False, default="blue")
    currency_unit: Mapped[str] = mapped_column(String(10), nullable=False, default="toman", server_default="toman")
    home_hero_badge: Mapped[str] = mapped_column(
        String(80), nullable=False, default="فروشگاه اینترنتی"
    )
    home_hero_title: Mapped[str] = mapped_column(
        String(160), nullable=False, default="خریدی ساده،\nانتخابی مطمئن"
    )
    home_hero_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="محصولات فروشگاه را ببینید، جست‌وجو کنید و گزینه‌ی مناسب خودتان را پیدا کنید.",
    )
    home_hero_button_label: Mapped[str] = mapped_column(
        String(50), nullable=False, default="مشاهده محصولات"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
