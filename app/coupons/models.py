from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.users.models import User


class Coupon(Base):
    __tablename__ = "coupons"

    __table_args__ = (
        CheckConstraint(
            "discount_value > 0",
            name="ck_coupons_discount_value_positive",
        ),
        CheckConstraint(
            "max_discount IS NULL OR max_discount >= 0",
            name="ck_coupons_max_discount_non_negative",
        ),
        CheckConstraint(
            "min_order_amount >= 0",
            name="ck_coupons_min_order_amount_non_negative",
        ),
        CheckConstraint(
            "max_uses IS NULL OR max_uses > 0",
            name="ck_coupons_max_uses_positive",
        ),
        CheckConstraint(
            "max_uses_per_user IS NULL OR max_uses_per_user > 0",
            name="ck_coupons_max_uses_per_user_positive",
        ),
        CheckConstraint(
            "used_count >= 0",
            name="ck_coupons_used_count_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )

    discount_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    discount_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 0),
        nullable=False,
    )

    max_discount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 0),
        nullable=True,
    )

    min_order_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 0),
        nullable=False,
        default=0,
    )

    max_uses: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    max_uses_per_user: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    used_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User | None"] = relationship(
        "User",
        back_populates="coupons",
    )

    usages: Mapped[list["CouponUsage"]] = relationship(
        back_populates="coupon",
        cascade="all, delete-orphan",
    )


class CouponUsage(Base):
    __tablename__ = "coupon_usages"

    __table_args__ = (
        UniqueConstraint(
            "order_id",
            name="uq_coupon_usages_order",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    coupon_id: Mapped[int] = mapped_column(
        ForeignKey("coupons.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="RESTRICT"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    coupon: Mapped["Coupon"] = relationship(
        back_populates="usages",
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="coupon_usages",
    )