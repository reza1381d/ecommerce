from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CouponCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=100)

    user_id: int | None = Field(
        default=None,
        gt=0,
    )

    discount_type: str
    discount_value: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    max_discount: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )

    min_order_amount: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        max_digits=12,
        decimal_places=2,
    )

    max_uses: int | None = Field(
        default=None,
        gt=0,
    )

    max_uses_per_user: int | None = Field(
        default=None,
        gt=0,
    )

    starts_at: datetime | None = None
    expires_at: datetime | None = None

    is_active: bool = True

    @model_validator(mode="after")
    def validate_coupon_rules(self):
        if self.discount_type not in {"percentage", "fixed"}:
            raise ValueError(
                "discount_type must be 'percentage' or 'fixed'"
            )

        if (
            self.discount_type == "percentage"
            and self.discount_value > 100
        ):
            raise ValueError(
                "Percentage discount cannot exceed 100"
            )

        if (
            self.starts_at is not None
            and self.expires_at is not None
            and self.expires_at <= self.starts_at
        ):
            raise ValueError(
                "expires_at must be later than starts_at"
            )

        return self


class CouponUpdateRequest(BaseModel):
    code: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    user_id: int | None = Field(
        default=None,
        gt=0,
    )

    discount_type: str | None = None

    discount_value: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    max_discount: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )

    min_order_amount: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )

    max_uses: int | None = Field(
        default=None,
        gt=0,
    )

    max_uses_per_user: int | None = Field(
        default=None,
        gt=0,
    )

    starts_at: datetime | None = None
    expires_at: datetime | None = None

    is_active: bool | None = None


class CouponResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    user_id: int | None
    discount_type: str
    discount_value: Decimal
    max_discount: Decimal | None
    min_order_amount: Decimal
    max_uses: int | None
    max_uses_per_user: int | None
    used_count: int
    starts_at: datetime | None
    expires_at: datetime | None
    is_active: bool


class CouponValidationResponse(BaseModel):
    valid: bool
    discount_amount: Decimal