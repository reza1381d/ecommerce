from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.exceptions import (
    InsufficientStockError,
    ReservationNotActiveError,
    ReservationNotExpiredError,
    ReservationNotFoundError,
)
from app.orders.models import Order, OrderItem
from app.orders.state_machine import OrderStatus
from app.products.models import Product
from app.reservations.models import Reservation
from app.reservations.service import ReservationService
from app.reservations.state_machine import ReservationStatus
from app.users.models import User


def create_user(db) -> User:
    user = User(
        email=f"test-{uuid4()}@example.com",
        password_hash="hashed_password",
        first_name="Test",
        last_name="User",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_product(
    db,
    *,
    stock: int = 10,
    reserved_stock: int = 0,
) -> Product:

    product = Product(
        name="Test Product",
        description="Test description",
        price=100,
        stock=stock,
        reserved_stock=reserved_stock,
        is_active=True,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


def create_order(
    db,
    *,
    user_id: int,
) -> Order:

    order = Order(
        user_id=user_id,
        status=OrderStatus.PENDING_PAYMENT.value,
        subtotal=Decimal("200.00"),
        discount_amount=Decimal("0.00"),
        shipping_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("200.00"),
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


def create_order_item(
    db,
    *,
    order: Order,
    product: Product,
    quantity: int = 2,
) -> OrderItem:

    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        product_name=product.name,
        unit_price=product.price,
        quantity=quantity,
        total_price=product.price * quantity,
    )

    db.add(order_item)
    db.commit()
    db.refresh(order_item)

    return order_item


def create_reservation(
    db,
    *,
    order_item: OrderItem,
    quantity: int = 2,
    status: str = ReservationStatus.ACTIVE.value,
    expires_at: datetime | None = None,
) -> Reservation:

    reservation = Reservation(
        order_item_id=order_item.id,
        quantity=quantity,
        status=status,
        expires_at=(
            expires_at
            or datetime.now(timezone.utc)
            - timedelta(minutes=1)
        ),
    )

    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    return reservation


def create_reservation_scenario(
    db,
    *,
    stock: int = 10,
    reserved_stock: int = 2,
    quantity: int = 2,
    status: str = ReservationStatus.ACTIVE.value,
    expires_at: datetime | None = None,
):
    user = create_user(db)

    product = create_product(
        db,
        stock=stock,
        reserved_stock=reserved_stock,
    )

    order = create_order(
        db,
        user_id=user.id,
    )

    order_item = create_order_item(
        db,
        order=order,
        product=product,
        quantity=quantity,
    )

    reservation = create_reservation(
        db,
        order_item=order_item,
        quantity=quantity,
        status=status,
        expires_at=expires_at,
    )

    return user, product, order, order_item, reservation


def test_expire_reservation_changes_status(db):

    _, _, _, _, reservation = create_reservation_scenario(
        db,
        stock=10,
        reserved_stock=2,
        quantity=2,
    )

    result = ReservationService.expire_reservation(
        db=db,
        reservation_id=reservation.id,
    )

    assert result.status == ReservationStatus.EXPIRED.value


def test_expire_reservation_releases_inventory(db):

    _, product, _, _, reservation = create_reservation_scenario(
        db,
        stock=10,
        reserved_stock=2,
        quantity=2,
    )

    ReservationService.expire_reservation(
        db=db,
        reservation_id=reservation.id,
    )

    db.refresh(product)

    assert product.stock == 10
    assert product.reserved_stock == 0


def test_expire_reservation_does_not_change_stock(db):

    _, product, _, _, reservation = create_reservation_scenario(
        db,
        stock=10,
        reserved_stock=3,
        quantity=3,
    )

    ReservationService.expire_reservation(
        db=db,
        reservation_id=reservation.id,
    )

    db.refresh(product)

    assert product.stock == 10


def test_cannot_expire_reservation_before_expiration(db):

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=10)
    )

    _, _, _, _, reservation = create_reservation_scenario(
        db,
        stock=10,
        reserved_stock=2,
        quantity=2,
        expires_at=expires_at,
    )

    with pytest.raises(
        ReservationNotExpiredError,
        match="has not expired yet",
    ):
        ReservationService.expire_reservation(
            db=db,
            reservation_id=reservation.id,
        )


@pytest.mark.parametrize(
    "status",
    [
        ReservationStatus.CONSUMED.value,
        ReservationStatus.EXPIRED.value,
    ],
)
def test_cannot_expire_non_active_reservation(
    db,
    status,
):

    _, _, _, _, reservation = create_reservation_scenario(
        db,
        stock=10,
        reserved_stock=0,
        quantity=2,
        status=status,
    )

    with pytest.raises(
        ReservationNotActiveError,
        match="not active",
    ):
        ReservationService.expire_reservation(
            db=db,
            reservation_id=reservation.id,
        )


def test_expire_nonexistent_reservation(db):

    with pytest.raises(
        ReservationNotFoundError,
        match="Reservation not found",
    ):
        ReservationService.expire_reservation(
            db=db,
            reservation_id=999999,
        )


def test_expiring_already_expired_reservation_does_not_release_again(
    db,
):

    _, product, _, _, reservation = create_reservation_scenario(
        db,
        stock=10,
        reserved_stock=2,
        quantity=2,
        status=ReservationStatus.EXPIRED.value,
    )

    with pytest.raises(
        ReservationNotActiveError,
        match="not active",
    ):
        ReservationService.expire_reservation(
            db=db,
            reservation_id=reservation.id,
        )

    db.refresh(product)

    assert product.reserved_stock == 2


def test_expire_reservation_rolls_back_when_inventory_release_fails(
    db,
):

    _, product, _, _, reservation = create_reservation_scenario(
        db,
        stock=10,
        reserved_stock=1,
        quantity=2,
    )

    with pytest.raises(InsufficientStockError):
        ReservationService.expire_reservation(
            db=db,
            reservation_id=reservation.id,
        )

    db.refresh(reservation)
    db.refresh(product)

    assert reservation.status == ReservationStatus.ACTIVE.value
    assert product.stock == 10
    assert product.reserved_stock == 1


def test_expire_due_reservations_expires_due_reservations(
    db,
):

    _, product_1, _, _, reservation_1 = (
        create_reservation_scenario(
            db,
            stock=10,
            reserved_stock=2,
            quantity=2,
        )
    )

    _, product_2, _, _, reservation_2 = (
        create_reservation_scenario(
            db,
            stock=20,
            reserved_stock=3,
            quantity=3,
        )
    )

    future_expiration = (
        datetime.now(timezone.utc)
        + timedelta(minutes=10)
    )

    _, product_3, _, _, reservation_3 = (
        create_reservation_scenario(
            db,
            stock=30,
            reserved_stock=4,
            quantity=4,
            expires_at=future_expiration,
        )
    )

    expired_count = ReservationService.expire_due_reservations(
        db=db,
    )

    assert expired_count == 2

    db.refresh(reservation_1)
    db.refresh(reservation_2)
    db.refresh(reservation_3)

    db.refresh(product_1)
    db.refresh(product_2)
    db.refresh(product_3)

    assert reservation_1.status == ReservationStatus.EXPIRED.value
    assert reservation_2.status == ReservationStatus.EXPIRED.value
    assert reservation_3.status == ReservationStatus.ACTIVE.value

    assert product_1.reserved_stock == 0
    assert product_2.reserved_stock == 0
    assert product_3.reserved_stock == 4


def test_expire_due_reservations_continues_after_failure(
    db,
):

    _, failed_product, _, _, failed_reservation = (
        create_reservation_scenario(
            db,
            stock=10,
            reserved_stock=1,
            quantity=2,
        )
    )

    _, successful_product, _, _, successful_reservation = (
        create_reservation_scenario(
            db,
            stock=10,
            reserved_stock=2,
            quantity=2,
        )
    )

    expired_count = ReservationService.expire_due_reservations(
        db=db,
    )

    assert expired_count == 1

    db.refresh(failed_reservation)
    db.refresh(successful_reservation)

    db.refresh(failed_product)
    db.refresh(successful_product)

    assert failed_reservation.status == ReservationStatus.ACTIVE.value
    assert successful_reservation.status == ReservationStatus.EXPIRED.value

    assert failed_product.stock == 10
    assert failed_product.reserved_stock == 1

    assert successful_product.stock == 10
    assert successful_product.reserved_stock == 0