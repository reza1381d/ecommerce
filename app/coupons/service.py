from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.cart.models import Cart, CartItem
from app.coupons.models import Coupon, CouponUsage
from app.coupons.schemas import (
    CouponCreateRequest,
    CouponUpdateRequest,
)
from app.core.exceptions import (
    CouponAlreadyExistsError,
    CouponAlreadyUsedError,
    CartEmptyError,
    CouponExpiredError,
    CouponInactiveError,
    CouponNotEligibleError,
    CouponNotFoundError,
    CouponNotStartedError,
    CouponUsageLimitError,
)
from app.products.models import Product


def create_coupon(
    db: Session,
    data: CouponCreateRequest,
) -> Coupon:
    existing_coupon = db.scalar(
        select(Coupon).where(
            Coupon.code == data.code,
        )
    )

    if existing_coupon:
        raise CouponAlreadyExistsError()

    coupon = Coupon(
        code=data.code,
        user_id=data.user_id,
        discount_type=data.discount_type,
        discount_value=data.discount_value,
        max_discount=data.max_discount,
        min_order_amount=data.min_order_amount,
        max_uses=data.max_uses,
        max_uses_per_user=data.max_uses_per_user,
        starts_at=data.starts_at,
        expires_at=data.expires_at,
        is_active=data.is_active,
    )

    db.add(coupon)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise CouponAlreadyExistsError()

    db.refresh(coupon)

    return coupon


def get_coupon(
    db: Session,
    coupon_id: int,
) -> Coupon:
    coupon = db.scalar(
        select(Coupon).where(
            Coupon.id == coupon_id,
        )
    )

    if coupon is None:
        raise CouponNotFoundError()

    return coupon


def get_coupon_by_code(
    db: Session,
    code: str,
) -> Coupon:
    coupon = db.scalar(
        select(Coupon).where(
            Coupon.code == code,
        )
    )

    if coupon is None:
        raise CouponNotFoundError()

    return coupon


def update_coupon(
    db: Session,
    coupon: Coupon,
    data: CouponUpdateRequest,
) -> Coupon:
    update_data = data.model_dump(
        exclude_unset=True,
    )

    if "code" in update_data:
        existing_coupon = db.scalar(
            select(Coupon).where(
                Coupon.code == update_data["code"],
                Coupon.id != coupon.id,
            )
        )

        if existing_coupon:
            raise CouponAlreadyExistsError()

    for field, value in update_data.items():
        setattr(coupon, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise CouponAlreadyExistsError()

    db.refresh(coupon)

    return coupon


def validate_coupon(
    db: Session,
    coupon: Coupon,
    user_id: int,
    order_amount: Decimal,
) -> None:
    if not coupon.is_active:
        raise CouponInactiveError()

    now = datetime.now(timezone.utc)

    if (
        coupon.starts_at is not None
        and now < coupon.starts_at
    ):
        raise CouponNotStartedError()

    if (
        coupon.expires_at is not None
        and now >= coupon.expires_at
    ):
        raise CouponExpiredError()

    if (
        coupon.user_id is not None
        and coupon.user_id != user_id
    ):
        raise CouponNotEligibleError()

    if order_amount < coupon.min_order_amount:
        raise CouponNotEligibleError()

    if (
        coupon.max_uses is not None
        and coupon.used_count >= coupon.max_uses
    ):
        raise CouponUsageLimitError()

    if coupon.max_uses_per_user is not None:
        user_usage_count = db.scalar(
            select(func.count(CouponUsage.id)).where(
                CouponUsage.coupon_id == coupon.id,
                CouponUsage.user_id == user_id,
            )
        )

        if (
            user_usage_count
            >= coupon.max_uses_per_user
        ):
            raise CouponUsageLimitError()


def calculate_discount(
    coupon: Coupon,
    order_amount: Decimal,
) -> Decimal:
    if coupon.discount_type == "percentage":
        discount = (
            order_amount
            * coupon.discount_value
            / Decimal("100")
        )

        if coupon.max_discount is not None:
            discount = min(
                discount,
                coupon.max_discount,
            )

    else:
        discount = coupon.discount_value

    discount = discount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return min(
        discount,
        order_amount,
    )


def preview_coupon_for_cart(
    db: Session,
    code: str,
    user_id: int,
):
    normalized_code = code.strip().upper()
    coupon = db.scalar(
        select(Coupon).where(
            func.upper(Coupon.code) == normalized_code,
        )
    )

    if coupon is None:
        raise CouponNotFoundError()

    cart = db.scalar(
        select(Cart).where(Cart.user_id == user_id)
    )
    if cart is None:
        raise CartEmptyError()

    cart_items = list(
        db.scalars(
            select(CartItem).where(CartItem.cart_id == cart.id)
        ).all()
    )
    if not cart_items:
        raise CartEmptyError()

    product_ids = [item.product_id for item in cart_items]
    products = list(
        db.scalars(select(Product).where(Product.id.in_(product_ids))).all()
    )
    products_by_id = {product.id: product for product in products}
    subtotal = Decimal("0")
    for item in cart_items:
        product = products_by_id.get(item.product_id)
        if product is None:
            raise CouponNotEligibleError()
        subtotal += product.price * item.quantity

    validate_coupon(db, coupon, user_id, subtotal)
    discount = calculate_discount(coupon, subtotal)
    return {
        "valid": True,
        "subtotal": subtotal,
        "discount_amount": discount,
        "total_amount": subtotal - discount,
    }


def consume_coupon(
    db: Session,
    coupon_id: int,
    user_id: int,
    order_id: int,
) -> CouponUsage:
    coupon = db.scalar(
        select(Coupon)
        .where(Coupon.id == coupon_id)
        .with_for_update()
    )

    if coupon is None:
        raise CouponNotFoundError()

    if coupon.max_uses is not None:
        if coupon.used_count >= coupon.max_uses:
            raise CouponUsageLimitError()

    if coupon.max_uses_per_user is not None:
        user_usage_count = db.scalar(
            select(func.count(CouponUsage.id)).where(
                CouponUsage.coupon_id == coupon.id,
                CouponUsage.user_id == user_id,
            )
        )

        if (
            user_usage_count
            >= coupon.max_uses_per_user
        ):
            raise CouponUsageLimitError()

    existing_usage = db.scalar(
        select(CouponUsage).where(
            CouponUsage.order_id == order_id,
        )
    )

    if existing_usage is not None:
        raise CouponAlreadyUsedError()

    coupon.used_count += 1

    usage = CouponUsage(
        coupon_id=coupon.id,
        user_id=user_id,
        order_id=order_id,
    )

    db.add(usage)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise CouponAlreadyUsedError()

    return usage
