from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.orders.models import Order
from app.orders.state_machine import OrderStatus
from app.orders.models import Order, OrderItem
from app.payments.models import Payment


PERIOD_DAYS = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
}

PAID_ORDER_STATUSES = {
    OrderStatus.PAID.value,
    OrderStatus.SHIPPED.value,
    OrderStatus.DELIVERED.value,
}


def _as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return date.fromisoformat(str(value))


def _as_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")

    return Decimal(str(value))


def get_dashboard_stats(
    db: Session,
    period: str,
) -> dict:
    days = PERIOD_DAYS[period]
    end_at = datetime.now(timezone.utc)
    first_day = end_at.date() - timedelta(days=days - 1)

    # بازه از نیمه‌شب UTC روز شروع محاسبه می‌شود.
    start_at = datetime.combine(
        first_day,
        time.min,
        tzinfo=timezone.utc,
    )

    order_day = func.date(Order.created_at)

    order_rows = db.execute(
        select(
            order_day.label("day"),
            Order.status,
            func.count(Order.id),
        )
        .where(
            Order.created_at >= start_at,
            Order.created_at <= end_at,
        )
        .group_by(order_day, Order.status)
    ).all()

    order_counts: dict[str, int] = {}
    daily_stats: dict[str, dict] = {}

    for day_value, status, count in order_rows:
        day_key = _as_date(day_value).isoformat()
        count = int(count)

        order_counts[status] = order_counts.get(status, 0) + count

        daily = daily_stats.setdefault(
            day_key,
            {
                "orders": 0,
                "paid_orders": 0,
                "revenue": Decimal("0"),
            },
        )

        daily["orders"] += count

        if status in PAID_ORDER_STATUSES:
            daily["paid_orders"] += count

    payment_day = func.date(Payment.created_at)

    payment_rows = db.execute(
        select(
            payment_day.label("day"),
            Payment.status,
            func.count(Payment.id),
            func.coalesce(func.sum(Payment.amount), 0),
        )
        .where(
            Payment.created_at >= start_at,
            Payment.created_at <= end_at,
        )
        .group_by(payment_day, Payment.status)
    ).all()

    payment_counts: dict[str, int] = {}
    total_revenue = Decimal("0")
    successful_payment_count = 0

    for day_value, status, count, amount in payment_rows:
        count = int(count)
        payment_counts[status] = payment_counts.get(status, 0) + count

        if status != "successful":
            continue

        day_key = _as_date(day_value).isoformat()
        revenue = _as_decimal(amount)

        total_revenue += revenue
        successful_payment_count += count

        daily = daily_stats.setdefault(
            day_key,
            {
                "orders": 0,
                "paid_orders": 0,
                "revenue": Decimal("0"),
            },
        )
        daily["revenue"] += revenue

    paid_orders = sum(
        order_counts.get(status, 0)
        for status in PAID_ORDER_STATUSES
    )

    average_successful_payment = (
        total_revenue / successful_payment_count
        if successful_payment_count
        else Decimal("0")
    )

    trend = []

    for offset in range(days):
        current_day = first_day + timedelta(days=offset)
        values = daily_stats.get(
            current_day.isoformat(),
            {
                "orders": 0,
                "paid_orders": 0,
                "revenue": Decimal("0"),
            },
        )

        trend.append(
            {
                "date": current_day,
                "orders": values["orders"],
                "paid_orders": values["paid_orders"],
                "revenue": values["revenue"],
            }
        )

    return {
        "period": period,
        "start_at": start_at,
        "end_at": end_at,
        "total_orders": sum(order_counts.values()),
        "pending_payment_orders": order_counts.get(
            OrderStatus.PENDING_PAYMENT.value,
            0,
        ),
        "paid_orders": paid_orders,
        "cancelled_orders": order_counts.get(
            OrderStatus.CANCELLED.value,
            0,
        ),
        "shipped_orders": order_counts.get(
            OrderStatus.SHIPPED.value,
            0,
        ),
        "delivered_orders": order_counts.get(
            OrderStatus.DELIVERED.value,
            0,
        ),
        "successful_payments": payment_counts.get("successful", 0),
        "pending_payments": payment_counts.get("pending", 0),
        "failed_payments": payment_counts.get("failed", 0),
        "total_revenue": total_revenue,
        "average_successful_payment": average_successful_payment,
        "trend": trend,
    }


def get_product_sales(
    db: Session,
    period: str,
    limit: int,
) -> dict:
    days = PERIOD_DAYS[period]
    end_at = datetime.now(timezone.utc)
    start_at = datetime.combine(
        end_at.date() - timedelta(days=days - 1),
        time.min,
        tzinfo=timezone.utc,
    )

    rows = db.execute(
        select(
            OrderItem.product_id,
            OrderItem.product_name,
            func.sum(OrderItem.quantity),
            func.count(func.distinct(Order.id)),
            func.coalesce(func.sum(OrderItem.total_price), 0),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .join(Payment, Payment.order_id == Order.id)
        .where(
            Payment.status == "successful",
            Payment.created_at >= start_at,
            Payment.created_at <= end_at,
        )
        .group_by(
            OrderItem.product_id,
            OrderItem.product_name,
        )
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
    ).all()

    return {
        "period": period,
        "items": [
            {
                "product_id": product_id,
                "product_name": product_name,
                "quantity_sold": int(quantity_sold or 0),
                "order_count": int(order_count or 0),
                "revenue": _as_decimal(revenue),
            }
            for (
                product_id,
                product_name,
                quantity_sold,
                order_count,
                revenue,
            ) in rows
        ],
    }


def get_sales_timeline(
    db: Session,
    group_by: str,
    limit: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    now = datetime.now(timezone.utc)

    if start_date is not None and end_date is not None:
        if group_by == "day":
            start_at = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
            end_exclusive = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
            keys = [
                (start_date + timedelta(days=offset)).isoformat()
                for offset in range((end_date - start_date).days + 1)
            ]
        elif group_by == "month":
            start_at = datetime(start_date.year, start_date.month, 1, tzinfo=timezone.utc)
            end_year = end_date.year + (1 if end_date.month == 12 else 0)
            end_month = 1 if end_date.month == 12 else end_date.month + 1
            end_exclusive = datetime(end_year, end_month, 1, tzinfo=timezone.utc)
            month_count = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
            keys = []
            for offset in range(month_count):
                index = start_date.year * 12 + start_date.month - 1 + offset
                year, month_index = divmod(index, 12)
                keys.append(f"{year:04d}-{month_index + 1:02d}")
        else:
            start_at = datetime(start_date.year, 1, 1, tzinfo=timezone.utc)
            end_exclusive = datetime(end_date.year + 1, 1, 1, tzinfo=timezone.utc)
            keys = [str(year) for year in range(start_date.year, end_date.year + 1)]
        effective_end_at = min(end_exclusive, now)
    elif group_by == "day":
        first_day = now.date() - timedelta(days=limit - 1)
        start_at = datetime.combine(
            first_day,
            time.min,
            tzinfo=timezone.utc,
        )
        keys = [
            (first_day + timedelta(days=offset)).isoformat()
            for offset in range(limit)
        ]
    elif group_by == "month":
        month_index = now.year * 12 + now.month - 1 - (limit - 1)
        start_year, start_month_index = divmod(month_index, 12)
        start_month = start_month_index + 1
        start_at = datetime(
            start_year, start_month, 1, tzinfo=timezone.utc
        )
        keys = []
        for offset in range(limit):
            index = start_year * 12 + start_month - 1 + offset
            year, month_index = divmod(index, 12)
            keys.append(f"{year:04d}-{month_index + 1:02d}")
    else:
        first_year = now.year - limit + 1
        start_at = datetime(first_year, 1, 1, tzinfo=timezone.utc)
        keys = [str(year) for year in range(first_year, now.year + 1)]

    bucket = func.date_trunc(group_by, Payment.created_at)
    payment_filter = [
        Payment.status == "successful",
        Payment.created_at >= start_at,
    ]
    if start_date is not None and end_date is not None:
        payment_filter.append(Payment.created_at < effective_end_at)
    else:
        payment_filter.append(Payment.created_at <= now)

    sales_rows = db.execute(
        select(
            bucket,
            func.count(func.distinct(Payment.order_id)),
            func.coalesce(func.sum(Payment.amount), 0),
        )
        .where(*payment_filter)
        .group_by(bucket)
        .order_by(bucket.asc())
    ).all()

    unit_rows = db.execute(
        select(
            bucket,
            func.coalesce(func.sum(OrderItem.quantity), 0),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .join(Payment, Payment.order_id == Order.id)
        .where(*payment_filter)
        .group_by(bucket)
        .order_by(bucket.asc())
    ).all()

    def bucket_key(value) -> str:
        if group_by == "day":
            return _as_date(value).isoformat()

        if isinstance(value, str):
            value = datetime.fromisoformat(value)

        if group_by == "month":
            return value.strftime("%Y-%m")

        return value.strftime("%Y")

    sales_by_key = {
        bucket_key(value): {
            "orders": int(order_count or 0),
            "revenue": _as_decimal(revenue),
        }
        for value, order_count, revenue in sales_rows
    }
    units_by_key = {
        bucket_key(value): int(units_sold or 0)
        for value, units_sold in unit_rows
    }

    return {
        "group_by": group_by,
        "items": [
            {
                "period": key,
                "orders": sales_by_key.get(key, {}).get("orders", 0),
                "units_sold": units_by_key.get(key, 0),
                "revenue": sales_by_key.get(key, {}).get(
                    "revenue",
                    Decimal("0"),
                ),
            }
            for key in keys
        ],
    }
