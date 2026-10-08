from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session, selectinload

from app.orders.models import Order
from app.payments.models import Payment
from app.users.models import User


def get_admin_orders(
    db: Session,
    page: int,
    limit: int,
    order_status: str | None = None,
    payment_status: str | None = None,
):
    conditions = []

    if order_status:
        conditions.append(Order.status == order_status)

    if payment_status == "unpaid":
        conditions.append(
            ~exists(
                select(Payment.id).where(
                    Payment.order_id == Order.id,
                    Payment.status == "successful",
                )
            )
        )
    elif payment_status:
        conditions.append(
            exists(
                select(Payment.id).where(
                    Payment.order_id == Order.id,
                    Payment.status == payment_status,
                )
            )
        )

    orders_query = (
        select(Order)
        .options(
            selectinload(Order.items),
            selectinload(Order.address),
        )
        .order_by(Order.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )

    total_query = select(func.count()).select_from(Order)

    if conditions:
        orders_query = orders_query.where(*conditions)
        total_query = total_query.where(*conditions)

    orders = list(db.scalars(orders_query).all())
    total = db.scalar(total_query) or 0

    if not orders:
        return [], total, {}, {}

    order_ids = [order.id for order in orders]
    user_ids = {order.user_id for order in orders}

    # آخرین تراکنش هر سفارش بر اساس شناسه پرداخت انتخاب می‌شود.
    payments = db.scalars(
        select(Payment)
        .where(Payment.order_id.in_(order_ids))
        .order_by(Payment.order_id, Payment.id.desc())
    ).all()

    latest_payments = {}
    for payment in payments:
        latest_payments.setdefault(payment.order_id, payment)

    customers = db.scalars(
        select(User).where(User.id.in_(user_ids))
    ).all()
    customers_by_id = {customer.id: customer for customer in customers}

    return orders, total, latest_payments, customers_by_id