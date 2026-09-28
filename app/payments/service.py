from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import (
    OrderAlreadyPaidError,
    OrderNotAwaitingPaymentError,
    OrderNotFoundError,
    PaymentNotFoundError,
)
from app.inventory.service import InventoryService
from app.orders.models import Order, OrderItem
from app.orders.service import transition_order_status
from app.orders.state_machine import OrderStatus
from app.payments.models import Payment
from app.reservations.state_machine import (
    ReservationStatus,
    validate_transition,
)
from app.users.models import User


def create_payment(
    db: Session,
    user: User,
    order_id: int,
) -> Payment:

    order = db.scalar(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(
                OrderItem.reservation
            )
        )
        .where(
            Order.id == order_id,
            Order.user_id == user.id,
        )
        .with_for_update()
    )

    if order is None:
        raise OrderNotFoundError()

    if order.status != OrderStatus.PENDING_PAYMENT:
        raise OrderNotAwaitingPaymentError()

    existing_successful_payment = db.scalar(
        select(Payment).where(
            Payment.order_id == order.id,
            Payment.status == "successful",
        )
    )

    if existing_successful_payment is not None:
        raise OrderAlreadyPaidError()

    try:
        for order_item in order.items:
            reservation = order_item.reservation

            if reservation is None:
                raise ValueError("Order item has no reservation")

            if reservation.status != ReservationStatus.ACTIVE.value:
                raise ValueError(
                    "Order reservation is not active"
                )

            validate_transition(
                current_status=reservation.status,
                new_status=ReservationStatus.CONSUMED,
            )

            InventoryService.consume(
                db=db,
                product_id=order_item.product_id,
                quantity=reservation.quantity,
            )

            reservation.status = ReservationStatus.CONSUMED.value

        transition_order_status(
            order=order,
            new_status=OrderStatus.PAID,
        )

        payment = Payment(
            order_id=order.id,
            amount=order.total_amount,
            status="successful",
            provider="mock",
            provider_payment_id=f"mock_{uuid4()}",
        )

        db.add(payment)

        db.commit()
        db.refresh(payment)

        return payment

    except Exception:
        db.rollback()
        raise


def get_payment(
    db: Session,
    user: User,
    payment_id: int,
) -> Payment:

    payment = db.scalar(
        select(Payment)
        .join(Order, Payment.order_id == Order.id)
        .where(
            Payment.id == payment_id,
            Order.user_id == user.id,
        )
    )

    if payment is None:
        raise PaymentNotFoundError()

    return payment


def get_order_payments(
    db: Session,
    user: User,
    order_id: int,
) -> list[Payment]:

    return db.scalars(
        select(Payment)
        .join(Order, Payment.order_id == Order.id)
        .where(
            Payment.order_id == order_id,
            Order.user_id == user.id,
        )
        .order_by(Payment.id)
    ).all()


def get_user_payments(
    db: Session,
    user: User,
) -> list[Payment]:

    return db.scalars(
        select(Payment)
        .join(Order, Payment.order_id == Order.id)
        .where(
            Order.user_id == user.id
        )
        .order_by(Payment.id)
    ).all()