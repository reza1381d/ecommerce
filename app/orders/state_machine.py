from enum import StrEnum


from app.core.exceptions import InvalidOrderTransitionError


class OrderStatus(StrEnum):
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


ALLOWED_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.PENDING_PAYMENT: frozenset(
        {
            OrderStatus.PAID,
            OrderStatus.CANCELLED,
        }
    ),
    OrderStatus.PAID: frozenset(
        {
            OrderStatus.SHIPPED,
        }
    ),
    OrderStatus.SHIPPED: frozenset(
        {
            OrderStatus.DELIVERED,
        }
    ),
    OrderStatus.DELIVERED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}


def validate_transition(
    current_status: str,
    new_status: str,
) -> None:
    try:
        current = OrderStatus(current_status)
        new = OrderStatus(new_status)
    except ValueError:
        raise InvalidOrderTransitionError()

    allowed_statuses = ALLOWED_TRANSITIONS[current]

    if new not in allowed_statuses:
        raise InvalidOrderTransitionError()