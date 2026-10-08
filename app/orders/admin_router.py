from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.core.database import get_db
from app.orders.admin_schemas import (
    AdminOrderCustomer,
    AdminOrderListResponse,
    AdminOrderPayment,
    AdminOrderResponse,
)
from app.orders.admin_service import get_admin_orders
from app.orders.schemas import OrderResponse
from app.users.models import User


router = APIRouter(
    prefix="/admin/orders",
    tags=["Admin Orders"],
)


@router.get(
    "",
    response_model=AdminOrderListResponse,
)
def list_all_orders(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    order_status: str | None = Query(default=None),
    payment_status: str | None = Query(default=None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    orders, total, latest_payments, customers_by_id = get_admin_orders(
        db=db,
        page=page,
        limit=limit,
        order_status=order_status,
        payment_status=payment_status,
    )

    items = []

    for order in orders:
        payment = latest_payments.get(order.id)
        customer = customers_by_id.get(order.user_id)

        # اطلاعات پایه سفارش از همان schema موجود استفاده می‌کند.
        order_data = OrderResponse.model_validate(order).model_dump()

        items.append(
            AdminOrderResponse(
                **order_data,
                customer=AdminOrderCustomer(
                    id=customer.id,
                    email=customer.email,
                    first_name=customer.first_name,
                    last_name=customer.last_name,
                ),
                payment_status=payment.status if payment else "unpaid",
                latest_payment=(
                    AdminOrderPayment.model_validate(payment)
                    if payment
                    else None
                ),
            )
        )

    return AdminOrderListResponse(
        items=items,
        page=page,
        limit=limit,
        total=total,
    )