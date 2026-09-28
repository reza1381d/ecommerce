import pytest

from app.core.exceptions import InvalidOrderTransitionError
from app.orders.models import Order
from app.orders.service import transition_order_status
from app.orders.state_machine import (
    OrderStatus,
    validate_transition,
)


# ============================================================
# State Machine Tests
# ============================================================


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        (
            OrderStatus.PENDING_PAYMENT,
            OrderStatus.PAID,
        ),
        (
            OrderStatus.PENDING_PAYMENT,
            OrderStatus.CANCELLED,
        ),
        (
            OrderStatus.PAID,
            OrderStatus.SHIPPED,
        ),
        (
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        ),
    ],
)
def test_valid_order_transition(
    current_status: OrderStatus,
    new_status: OrderStatus,
):
    validate_transition(
        current_status=current_status.value,
        new_status=new_status.value,
    )


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        (
            OrderStatus.PENDING_PAYMENT,
            OrderStatus.SHIPPED,
        ),
        (
            OrderStatus.PENDING_PAYMENT,
            OrderStatus.DELIVERED,
        ),
        (
            OrderStatus.PAID,
            OrderStatus.CANCELLED,
        ),
        (
            OrderStatus.PAID,
            OrderStatus.DELIVERED,
        ),
        (
            OrderStatus.SHIPPED,
            OrderStatus.PAID,
        ),
        (
            OrderStatus.SHIPPED,
            OrderStatus.CANCELLED,
        ),
        (
            OrderStatus.DELIVERED,
            OrderStatus.PENDING_PAYMENT,
        ),
        (
            OrderStatus.DELIVERED,
            OrderStatus.PAID,
        ),
        (
            OrderStatus.DELIVERED,
            OrderStatus.SHIPPED,
        ),
        (
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED,
        ),
        (
            OrderStatus.CANCELLED,
            OrderStatus.PENDING_PAYMENT,
        ),
        (
            OrderStatus.CANCELLED,
            OrderStatus.PAID,
        ),
        (
            OrderStatus.CANCELLED,
            OrderStatus.SHIPPED,
        ),
        (
            OrderStatus.CANCELLED,
            OrderStatus.DELIVERED,
        ),
    ],
)
def test_invalid_order_transition(
    current_status: OrderStatus,
    new_status: OrderStatus,
):
    with pytest.raises(InvalidOrderTransitionError):
        validate_transition(
            current_status=current_status.value,
            new_status=new_status.value,
        )


@pytest.mark.parametrize(
    "status",
    [
        OrderStatus.PENDING_PAYMENT,
        OrderStatus.PAID,
        OrderStatus.SHIPPED,
        OrderStatus.DELIVERED,
        OrderStatus.CANCELLED,
    ],
)
def test_same_status_transition_is_invalid(status: OrderStatus):
    with pytest.raises(InvalidOrderTransitionError):
        validate_transition(
            current_status=status.value,
            new_status=status.value,
        )


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        ("unknown", OrderStatus.PAID.value),
        (OrderStatus.PENDING_PAYMENT.value, "unknown"),
        ("invalid", "unknown"),
    ],
)
def test_unknown_status_is_invalid(
    current_status: str,
    new_status: str,
):
    with pytest.raises(InvalidOrderTransitionError):
        validate_transition(
            current_status=current_status,
            new_status=new_status,
        )


# ============================================================
# transition_order_status Service Tests
# ============================================================


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        (
            OrderStatus.PENDING_PAYMENT,
            OrderStatus.PAID,
        ),
        (
            OrderStatus.PENDING_PAYMENT,
            OrderStatus.CANCELLED,
        ),
        (
            OrderStatus.PAID,
            OrderStatus.SHIPPED,
        ),
        (
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        ),
    ],
)
def test_transition_order_status_success(
    current_status: OrderStatus,
    new_status: OrderStatus,
):
    order = Order(status=current_status.value)

    transition_order_status(
        order=order,
        new_status=new_status,
    )

    assert order.status == new_status.value


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        (
            OrderStatus.PENDING_PAYMENT,
            OrderStatus.SHIPPED,
        ),
        (
            OrderStatus.PENDING_PAYMENT,
            OrderStatus.DELIVERED,
        ),
        (
            OrderStatus.PAID,
            OrderStatus.CANCELLED,
        ),
        (
            OrderStatus.PAID,
            OrderStatus.DELIVERED,
        ),
        (
            OrderStatus.SHIPPED,
            OrderStatus.PAID,
        ),
        (
            OrderStatus.SHIPPED,
            OrderStatus.CANCELLED,
        ),
        (
            OrderStatus.DELIVERED,
            OrderStatus.PENDING_PAYMENT,
        ),
        (
            OrderStatus.CANCELLED,
            OrderStatus.PAID,
        ),
    ],
)
def test_invalid_transition_order_status_does_not_change_status(
    current_status: OrderStatus,
    new_status: OrderStatus,
):
    order = Order(status=current_status.value)

    with pytest.raises(InvalidOrderTransitionError):
        transition_order_status(
            order=order,
            new_status=new_status,
        )

    assert order.status == current_status.value


@pytest.mark.parametrize(
    "status",
    [
        OrderStatus.PENDING_PAYMENT,
        OrderStatus.PAID,
        OrderStatus.SHIPPED,
        OrderStatus.DELIVERED,
        OrderStatus.CANCELLED,
    ],
)
def test_transition_order_status_same_status_is_invalid(
    status: OrderStatus,
):
    order = Order(status=status.value)

    with pytest.raises(InvalidOrderTransitionError):
        transition_order_status(
            order=order,
            new_status=status,
        )

    assert order.status == status.value
