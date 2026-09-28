from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi import status

from app.auth.security import create_access_token, hash_password
from app.coupons.models import Coupon, CouponUsage
from app.coupons.schemas import CouponCreateRequest
from app.coupons.service import (
    calculate_discount,
    consume_coupon,
    create_coupon,
    validate_coupon,
)
from app.core.exceptions import (
    CouponAlreadyUsedError,
    CouponExpiredError,
    CouponInactiveError,
    CouponNotEligibleError,
    CouponNotStartedError,
    CouponUsageLimitError,
)
from app.orders.models import Order
from app.users.models import User


def create_user(
    db,
    *,
    email="user@example.com",
    role="customer",
):
    user = User(
        email=email,
        password_hash=hash_password("password123"),
        first_name="Test",
        last_name="User",
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_auth_headers(user):
    token = create_access_token(user.id)

    return {
        "Authorization": f"Bearer {token}",
    }


def create_order(
    db,
    user_id,
):
    order = Order(
        user_id=user_id,
        status="pending_payment",
        subtotal=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        shipping_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


# ============================================================
# Router - Create
# ============================================================


def test_admin_can_create_coupon(client, db):
    admin = create_user(
        db,
        email="admin@example.com",
        role="admin",
    )

    response = client.post(
        "/coupons",
        headers=get_auth_headers(admin),
        json={
            "code": "SUMMER20",
            "discount_type": "percentage",
            "discount_value": "20",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    assert data["code"] == "SUMMER20"
    assert data["discount_type"] == "percentage"
    assert Decimal(data["discount_value"]) == Decimal("20.00")
    assert data["used_count"] == 0
    assert data["is_active"] is True


def test_customer_cannot_create_coupon(client, db):
    user = create_user(
        db,
        role="customer",
    )

    response = client.post(
        "/coupons",
        headers=get_auth_headers(user),
        json={
            "code": "SUMMER20",
            "discount_type": "percentage",
            "discount_value": "20",
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_unauthenticated_user_cannot_create_coupon(client):
    response = client.post(
        "/coupons",
        json={
            "code": "SUMMER20",
            "discount_type": "percentage",
            "discount_value": "20",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_duplicate_coupon_code_returns_conflict(client, db):
    admin = create_user(
        db,
        email="admin@example.com",
        role="admin",
    )

    payload = {
        "code": "SUMMER20",
        "discount_type": "percentage",
        "discount_value": "20",
    }

    first_response = client.post(
        "/coupons",
        headers=get_auth_headers(admin),
        json=payload,
    )

    second_response = client.post(
        "/coupons",
        headers=get_auth_headers(admin),
        json=payload,
    )

    assert first_response.status_code == status.HTTP_201_CREATED
    assert second_response.status_code == status.HTTP_409_CONFLICT


# ============================================================
# Router - Get
# ============================================================


def test_admin_can_get_coupon_by_id(client, db):
    admin = create_user(
        db,
        email="admin@example.com",
        role="admin",
    )

    coupon = Coupon(
        code="TEST10",
        discount_type="percentage",
        discount_value=Decimal("10.00"),
    )

    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    response = client.get(
        f"/coupons/{coupon.id}",
        headers=get_auth_headers(admin),
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == coupon.id
    assert data["code"] == "TEST10"


def test_admin_can_get_coupon_by_code(client, db):
    admin = create_user(
        db,
        email="admin@example.com",
        role="admin",
    )

    coupon = Coupon(
        code="WELCOME10",
        discount_type="percentage",
        discount_value=Decimal("10.00"),
    )

    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    response = client.get(
        "/coupons/code/WELCOME10",
        headers=get_auth_headers(admin),
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == coupon.id
    assert data["code"] == "WELCOME10"


def test_get_nonexistent_coupon_returns_404(client, db):
    admin = create_user(
        db,
        email="admin@example.com",
        role="admin",
    )

    response = client.get(
        "/coupons/999999",
        headers=get_auth_headers(admin),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_nonexistent_coupon_by_code_returns_404(client, db):
    admin = create_user(
        db,
        email="admin@example.com",
        role="admin",
    )

    response = client.get(
        "/coupons/code/DOESNOTEXIST",
        headers=get_auth_headers(admin),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================
# Router - Update
# ============================================================


def test_admin_can_update_coupon(client, db):
    admin = create_user(
        db,
        email="admin@example.com",
        role="admin",
    )

    coupon = Coupon(
        code="OLD10",
        discount_type="percentage",
        discount_value=Decimal("10.00"),
    )

    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    response = client.patch(
        f"/coupons/{coupon.id}",
        headers=get_auth_headers(admin),
        json={
            "code": "NEW20",
            "discount_value": "20",
        },
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["code"] == "NEW20"
    assert Decimal(data["discount_value"]) == Decimal("20.00")


def test_customer_cannot_update_coupon(client, db):
    admin = create_user(
        db,
        email="admin@example.com",
        role="admin",
    )

    customer = create_user(
        db,
        email="customer@example.com",
        role="customer",
    )

    coupon = Coupon(
        code="TEST10",
        discount_type="percentage",
        discount_value=Decimal("10.00"),
    )

    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    response = client.patch(
        f"/coupons/{coupon.id}",
        headers=get_auth_headers(customer),
        json={
            "discount_value": "20",
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================
# Schema Validation
# ============================================================


@pytest.mark.parametrize(
    "payload",
    [
        {
            "code": "INVALID",
            "discount_type": "percentage",
            "discount_value": "101",
        },
        {
            "code": "INVALID",
            "discount_type": "unknown",
            "discount_value": "10",
        },
        {
            "code": "INVALID",
            "discount_type": "percentage",
            "discount_value": "10",
            "starts_at": "2026-10-10T00:00:00Z",
            "expires_at": "2026-10-01T00:00:00Z",
        },
    ],
)
def test_invalid_coupon_data_returns_422(client, db, payload):
    admin = create_user(
        db,
        email="admin@example.com",
        role="admin",
    )

    response = client.post(
        "/coupons",
        headers=get_auth_headers(admin),
        json=payload,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================
# Service - Discount Calculation
# ============================================================


def test_percentage_discount():
    coupon = Coupon(
        code="PERCENT20",
        discount_type="percentage",
        discount_value=Decimal("20"),
    )

    discount = calculate_discount(
        coupon,
        Decimal("100"),
    )

    assert discount == Decimal("20")


def test_percentage_discount_respects_max_discount():
    coupon = Coupon(
        code="PERCENT20",
        discount_type="percentage",
        discount_value=Decimal("20"),
        max_discount=Decimal("15"),
    )

    discount = calculate_discount(
        coupon,
        Decimal("100"),
    )

    assert discount == Decimal("15")


def test_fixed_discount():
    coupon = Coupon(
        code="FIXED30",
        discount_type="fixed",
        discount_value=Decimal("30"),
    )

    discount = calculate_discount(
        coupon,
        Decimal("100"),
    )

    assert discount == Decimal("30")


def test_discount_cannot_exceed_order_amount():
    coupon = Coupon(
        code="FIXED200",
        discount_type="fixed",
        discount_value=Decimal("200"),
    )

    discount = calculate_discount(
        coupon,
        Decimal("100"),
    )

    assert discount == Decimal("100")


# ============================================================
# Service - Validation
# ============================================================


def test_inactive_coupon_is_rejected(db):
    user = create_user(db)

    coupon = Coupon(
        code="INACTIVE",
        discount_type="percentage",
        discount_value=Decimal("10"),
        is_active=False,
    )

    db.add(coupon)
    db.commit()

    with pytest.raises(CouponInactiveError):
        validate_coupon(
            db,
            coupon,
            user.id,
            Decimal("100"),
        )


def test_coupon_before_start_date_is_rejected(db):
    user = create_user(db)

    coupon = Coupon(
        code="FUTURE",
        discount_type="percentage",
        discount_value=Decimal("10"),
        starts_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    db.add(coupon)
    db.commit()

    with pytest.raises(CouponNotStartedError):
        validate_coupon(
            db,
            coupon,
            user.id,
            Decimal("100"),
        )


def test_expired_coupon_is_rejected(db):
    user = create_user(db)

    coupon = Coupon(
        code="EXPIRED",
        discount_type="percentage",
        discount_value=Decimal("10"),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )

    db.add(coupon)
    db.commit()

    with pytest.raises(CouponExpiredError):
        validate_coupon(
            db,
            coupon,
            user.id,
            Decimal("100"),
        )


def test_user_specific_coupon_rejects_other_user(db):
    owner = create_user(
        db,
        email="owner@example.com",
    )

    other_user = create_user(
        db,
        email="other@example.com",
    )

    coupon = Coupon(
        code="PRIVATE10",
        user_id=owner.id,
        discount_type="percentage",
        discount_value=Decimal("10"),
    )

    db.add(coupon)
    db.commit()

    with pytest.raises(CouponNotEligibleError):
        validate_coupon(
            db,
            coupon,
            other_user.id,
            Decimal("100"),
        )


def test_order_below_minimum_amount_is_rejected(db):
    user = create_user(db)

    coupon = Coupon(
        code="MIN100",
        discount_type="percentage",
        discount_value=Decimal("10"),
        min_order_amount=Decimal("100"),
    )

    db.add(coupon)
    db.commit()

    with pytest.raises(CouponNotEligibleError):
        validate_coupon(
            db,
            coupon,
            user.id,
            Decimal("50"),
        )


def test_global_usage_limit_is_enforced(db):
    user = create_user(db)

    coupon = Coupon(
        code="LIMIT1",
        discount_type="percentage",
        discount_value=Decimal("10"),
        max_uses=1,
        used_count=1,
    )

    db.add(coupon)
    db.commit()

    with pytest.raises(CouponUsageLimitError):
        validate_coupon(
            db,
            coupon,
            user.id,
            Decimal("100"),
        )


def test_per_user_usage_limit_is_enforced(db):
    user = create_user(db)

    coupon = Coupon(
        code="USERLIMIT",
        discount_type="percentage",
        discount_value=Decimal("10"),
        max_uses_per_user=1,
    )

    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    order = create_order(
        db,
        user.id,
    )

    usage = CouponUsage(
        coupon_id=coupon.id,
        user_id=user.id,
        order_id=order.id,
    )

    coupon.used_count = 1

    db.add(usage)
    db.commit()

    with pytest.raises(CouponUsageLimitError):
        validate_coupon(
            db,
            coupon,
            user.id,
            Decimal("100"),
        )


# ============================================================
# Service - Consume Coupon
# ============================================================


def test_consume_coupon_increments_used_count(db):
    user = create_user(db)

    coupon = Coupon(
        code="CONSUME10",
        discount_type="percentage",
        discount_value=Decimal("10"),
        max_uses=5,
    )

    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    order = create_order(
        db,
        user.id,
    )

    usage = consume_coupon(
        db,
        coupon.id,
        user.id,
        order.id,
    )

    db.commit()

    assert usage.coupon_id == coupon.id
    assert usage.user_id == user.id
    assert usage.order_id == order.id
    assert coupon.used_count == 1


def test_same_order_cannot_use_two_coupons(db):
    user = create_user(db)

    first_coupon = Coupon(
        code="FIRST10",
        discount_type="percentage",
        discount_value=Decimal("10"),
    )

    second_coupon = Coupon(
        code="SECOND10",
        discount_type="percentage",
        discount_value=Decimal("10"),
    )

    db.add_all(
        [
            first_coupon,
            second_coupon,
        ]
    )

    db.commit()

    db.refresh(first_coupon)
    db.refresh(second_coupon)

    order = create_order(
        db,
        user.id,
    )

    consume_coupon(
        db,
        first_coupon.id,
        user.id,
        order.id,
    )

    db.commit()

    with pytest.raises(CouponAlreadyUsedError):
        consume_coupon(
            db,
            second_coupon.id,
            user.id,
            order.id,
        )


def test_consume_coupon_enforces_global_limit(db):
    user = create_user(db)

    coupon = Coupon(
        code="ONLYONE",
        discount_type="percentage",
        discount_value=Decimal("10"),
        max_uses=1,
        used_count=1,
    )

    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    order = create_order(
        db,
        user.id,
    )

    with pytest.raises(CouponUsageLimitError):
        consume_coupon(
            db,
            coupon.id,
            user.id,
            order.id,
        )


def test_consume_coupon_enforces_per_user_limit(db):
    user = create_user(db)

    coupon = Coupon(
        code="ONCEUSER",
        discount_type="percentage",
        discount_value=Decimal("10"),
        max_uses_per_user=1,
        used_count=1,
    )

    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    first_order = create_order(
        db,
        user.id,
    )

    existing_usage = CouponUsage(
        coupon_id=coupon.id,
        user_id=user.id,
        order_id=first_order.id,
    )

    db.add(existing_usage)
    db.commit()

    second_order = create_order(
        db,
        user.id,
    )

    with pytest.raises(CouponUsageLimitError):
        consume_coupon(
            db,
            coupon.id,
            user.id,
            second_order.id,
        )