from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.addresses.models import Address
from app.cart.models import Cart, CartItem
from app.core.exceptions import (
    AddressNotFoundError,
    CartEmptyError,
    InsufficientStockError,
    OrderNotFoundError,
    ProductInactiveError,
    ProductNotFoundError,
)
from app.inventory.service import InventoryService
from app.orders.models import Order, OrderAddress, OrderItem
from app.orders.state_machine import (
    OrderStatus,
    validate_transition,
)
from app.products.models import Product
from app.reservations.models import Reservation
from app.reservations.state_machine import ReservationStatus


RESERVATION_DURATION_MINUTES = 15


def transition_order_status(
    order: Order,
    new_status: OrderStatus,
) -> None:

    validate_transition(
        current_status=order.status,
        new_status=new_status,
    )

    order.status = new_status.value


def checkout(
    db: Session,
    user_id: int,
    address_id: int,
) -> Order:

    try:
        address = db.scalar(
            select(Address).where(
                Address.id == address_id,
                Address.user_id == user_id,
            )
        )

        if address is None:
            raise AddressNotFoundError()

        cart = db.scalar(
            select(Cart).where(
                Cart.user_id == user_id
            )
        )

        if cart is None:
            raise CartEmptyError()

        cart_items = list(
            db.scalars(
                select(CartItem).where(
                    CartItem.cart_id == cart.id
                )
            ).all()
        )

        if not cart_items:
            raise CartEmptyError()

        product_ids = [
            item.product_id
            for item in cart_items
        ]

        products = list(
            db.scalars(
                select(Product).where(
                    Product.id.in_(product_ids)
                )
            ).all()
        )

        products_by_id = {
            product.id: product
            for product in products
        }

        subtotal = Decimal("0.00")

        order = Order(
            user_id=user_id,
            status=OrderStatus.PENDING_PAYMENT.value,
            subtotal=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            shipping_amount=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("0.00"),
        )

        db.add(order)
        db.flush()

        order.address = OrderAddress(
            recipient_name=address.recipient_name,
            phone=address.phone,
            province=address.province,
            city=address.city,
            address_line=address.address_line,
            postal_code=address.postal_code,
        )

        for cart_item in cart_items:

            product = products_by_id.get(
                cart_item.product_id
            )

            if product is None:
                raise ProductNotFoundError()

            if not product.is_active:
                raise ProductInactiveError()

            item_total = (
                product.price * cart_item.quantity
            )

            order_item = OrderItem(
                order=order,
                product_id=product.id,
                product_name=product.name,
                unit_price=product.price,
                quantity=cart_item.quantity,
                total_price=item_total,
            )

            db.add(order_item)

            db.flush([order_item])

            InventoryService.reserve(
                db=db,
                product_id=product.id,
                quantity=cart_item.quantity,
            )

            reservation = Reservation(
                order_item_id=order_item.id,
                quantity=cart_item.quantity,
                status=ReservationStatus.ACTIVE.value,
                expires_at=(
                    datetime.now(timezone.utc)
                    + timedelta(
                        minutes=RESERVATION_DURATION_MINUTES
                    )
                ),
            )

            db.add(reservation)

            subtotal += item_total

        order.subtotal = subtotal

        order.total_amount = (
            subtotal
            - order.discount_amount
            + order.shipping_amount
            + order.tax_amount
        )

        db.execute(
            delete(CartItem).where(
                CartItem.cart_id == cart.id
            )
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    db.refresh(order)

    return order


def get_order(
    db: Session,
    user_id: int,
    order_id: int,
) -> Order:

    order = db.scalar(
        select(Order)
        .options(
            selectinload(Order.items),
            selectinload(Order.address),
        )
        .where(
            Order.id == order_id,
            Order.user_id == user_id,
        )
    )

    if order is None:
        raise OrderNotFoundError()

    return order


def get_user_orders(
    db: Session,
    user_id: int,
    page: int,
    limit: int,
) -> tuple[list[Order], int]:

    offset = (page - 1) * limit

    orders = list(
        db.scalars(
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.address),
            )
            .where(
                Order.user_id == user_id
            )
            .order_by(Order.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()
    )

    total = db.scalar(
        select(func.count())
        .select_from(Order)
        .where(
            Order.user_id == user_id
        )
    )

    return orders, total


def cancel_order(
    db: Session,
    user_id: int,
    order_id: int,
) -> Order:

    order = db.scalar(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == user_id,
        )
    )

    if order is None:
        raise OrderNotFoundError()

    try:
        transition_order_status(
            order=order,
            new_status=OrderStatus.CANCELLED,
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    db.refresh(order)

    return order