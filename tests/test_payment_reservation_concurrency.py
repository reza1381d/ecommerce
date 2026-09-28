from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, sessionmaker

from app.inventory.service import InventoryService
from app.orders.models import Order, OrderItem
from app.orders.state_machine import OrderStatus
from app.payments.models import Payment
from app.payments.service import create_payment
from app.products.models import Product
from app.reservations.models import Reservation
from app.reservations.service import ReservationService
from app.reservations.state_machine import ReservationStatus
from app.users.models import User


def create_user(db: Session) -> User:
    user = User(
        email=f"concurrency-{uuid4()}@example.com",
        password_hash="hashed_password",
        first_name="Concurrency",
        last_name="Test",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_product(db: Session) -> Product:
    product = Product(
        name="Concurrency Product",
        description="Concurrency test product",
        price=Decimal("100.00"),
        stock=10,
        reserved_stock=2,
        is_active=True,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


def create_order(
    db: Session,
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
    db: Session,
    *,
    order: Order,
    product: Product,
) -> OrderItem:
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        product_name=product.name,
        unit_price=product.price,
        quantity=2,
        total_price=Decimal("200.00"),
    )

    db.add(order_item)
    db.commit()
    db.refresh(order_item)

    return order_item


def create_reservation(
    db: Session,
    *,
    order_item: OrderItem,
) -> Reservation:
    reservation = Reservation(
        order_item_id=order_item.id,
        quantity=2,
        status=ReservationStatus.ACTIVE.value,
        expires_at=(
            datetime.now(timezone.utc)
            - timedelta(minutes=1)
        ),
    )

    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    return reservation


def get_final_order(
    db: Session,
    order_id: int,
) -> Order:
    order = db.scalar(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(
                OrderItem.reservation
            )
        )
        .where(Order.id == order_id)
    )

    assert order is not None

    return order


def test_payment_and_expiration_are_concurrency_safe(
    db: Session,
    monkeypatch,
):
    user = create_user(db)

    product = create_product(db)

    order = create_order(
        db,
        user_id=user.id,
    )

    order_item = create_order_item(
        db,
        order=order,
        product=product,
    )

    reservation = create_reservation(
        db,
        order_item=order_item,
    )

    session_factory = sessionmaker(
        bind=db.get_bind(),
        autocommit=False,
        autoflush=False,
    )

    payment_session = session_factory()
    expiration_session = session_factory()

    inventory_barrier = Barrier(2)

    original_consume = InventoryService.consume
    original_release = InventoryService.release

    def synchronized_consume(
        db,
        product_id,
        quantity,
    ):
        inventory_barrier.wait()

        return original_consume(
            db=db,
            product_id=product_id,
            quantity=quantity,
        )

    def synchronized_release(
        db,
        product_id,
        quantity,
    ):
        inventory_barrier.wait()

        return original_release(
            db=db,
            product_id=product_id,
            quantity=quantity,
        )

    monkeypatch.setattr(
        InventoryService,
        "consume",
        synchronized_consume,
    )

    monkeypatch.setattr(
        InventoryService,
        "release",
        synchronized_release,
    )

    payment_error = None
    expiration_error = None
    payment_result = None
    expiration_result = None

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            payment_future = executor.submit(
                create_payment,
                payment_session,
                user,
                order.id,
            )

            expiration_future = executor.submit(
                ReservationService.expire_reservation,
                expiration_session,
                reservation.id,
            )

            try:
                payment_result = payment_future.result(
                    timeout=10,
                )
            except Exception as exc:
                payment_error = exc

            try:
                expiration_result = expiration_future.result(
                    timeout=10,
                )
            except Exception as exc:
                expiration_error = exc

        successful_operations = sum(
            result is not None
            for result in (
                payment_result,
                expiration_result,
            )
        )

        assert successful_operations == 1

        db.expire_all()

        final_product = db.scalar(
            select(Product).where(
                Product.id == product.id,
            )
        )

        assert final_product is not None

        final_order = get_final_order(
            db,
            order.id,
        )

        final_reservation = final_order.items[0].reservation

        assert final_reservation is not None

        assert final_product.reserved_stock == 0

        if payment_result is not None:
            assert payment_error is None
            assert expiration_result is None

            assert (
                final_order.status
                == OrderStatus.PAID.value
            )

            assert (
                final_reservation.status
                == ReservationStatus.CONSUMED.value
            )

            assert final_product.stock == 8

            payment = db.scalar(
                select(Payment).where(
                    Payment.order_id == order.id,
                )
            )

            assert payment is not None

        else:
            assert expiration_error is None
            assert payment_result is None

            assert (
                final_order.status
                == OrderStatus.PENDING_PAYMENT.value
            )

            assert (
                final_reservation.status
                == ReservationStatus.EXPIRED.value
            )

            assert final_product.stock == 10

            payment = db.scalar(
                select(Payment).where(
                    Payment.order_id == order.id,
                )
            )

            assert payment is None

    finally:
        payment_session.close()
        expiration_session.close()