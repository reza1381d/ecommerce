from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from app.orders.models import Order
from app.payments.models import Payment
from app.users.models import User


SORT_COLUMNS = {
    "id": Payment.id,
    "order_id": Payment.order_id,
    "amount": Payment.amount,
    "status": func.lower(Payment.status),
    "provider": func.lower(Payment.provider),
    "created_at": Payment.created_at,
}


def list_admin_payments(
    db: Session,
    page: int,
    limit: int,
    search: str | None,
    payment_status: str | None,
    provider: str | None,
    order_id: int | None,
    sort_by: str,
    sort_order: str,
):
    conditions = []

    if payment_status:
        conditions.append(Payment.status == payment_status)

    if provider:
        conditions.append(Payment.provider == provider)

    if order_id is not None:
        conditions.append(Payment.order_id == order_id)

    if search and search.strip():
        term = search.strip()
        escaped_term = (
            term.replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )
        pattern = f"%{escaped_term}%"

        search_conditions = [
            cast(Payment.id, String).ilike(pattern, escape="\\"),
            cast(Payment.order_id, String).ilike(pattern, escape="\\"),
            cast(User.id, String).ilike(pattern, escape="\\"),
            User.email.ilike(pattern, escape="\\"),
            User.first_name.ilike(pattern, escape="\\"),
            User.last_name.ilike(pattern, escape="\\"),
            Payment.status.ilike(pattern, escape="\\"),
            Payment.provider.ilike(pattern, escape="\\"),
            Payment.provider_payment_id.ilike(pattern, escape="\\"),
        ]
        conditions.append(or_(*search_conditions))

    statement = (
        select(Payment, Order, User)
        .join(Order, Payment.order_id == Order.id)
        .join(User, Order.user_id == User.id)
    )
    count_statement = (
        select(func.count(Payment.id))
        .select_from(Payment)
        .join(Order, Payment.order_id == Order.id)
        .join(User, Order.user_id == User.id)
    )

    if conditions:
        statement = statement.where(*conditions)
        count_statement = count_statement.where(*conditions)

    sort_column = SORT_COLUMNS[sort_by]
    ordering = (
        sort_column.desc()
        if sort_order == "desc"
        else sort_column.asc()
    )

    statement = statement.order_by(ordering)
    if sort_by != "id":
        statement = statement.order_by(Payment.id.asc())

    offset = (page - 1) * limit
    rows = db.execute(
        statement.offset(offset).limit(limit)
    ).all()
    total = db.scalar(count_statement) or 0

    return rows, total