from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.core.database import get_db
from app.payments.admin_schemas import (
    AdminPaymentCustomer,
    AdminPaymentListResponse,
    AdminPaymentResponse,
)
from app.payments.admin_service import list_admin_payments
from app.users.models import User


router = APIRouter(
    prefix="/admin/payments",
    tags=["Admin Payments"],
)


@router.get(
    "",
    response_model=AdminPaymentListResponse,
)
def get_all_payments(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=200),
    payment_status: str | None = Query(default=None, max_length=30),
    provider: str | None = Query(default=None, max_length=50),
    order_id: int | None = Query(default=None, ge=1),
    sort_by: Literal[
        "id",
        "order_id",
        "amount",
        "status",
        "provider",
        "created_at",
    ] = Query(default="created_at"),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    rows, total = list_admin_payments(
        db=db,
        page=page,
        limit=limit,
        search=search,
        payment_status=payment_status,
        provider=provider,
        order_id=order_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    items = [
        AdminPaymentResponse(
            id=payment.id,
            order_id=payment.order_id,
            amount=payment.amount,
            status=payment.status,
            provider=payment.provider,
            provider_payment_id=payment.provider_payment_id,
            created_at=payment.created_at,
            order_status=order.status,
            customer=AdminPaymentCustomer(
                id=customer.id,
                email=customer.email,
                first_name=customer.first_name,
                last_name=customer.last_name,
                phone=customer.phone,
            ),
        )
        for payment, order, customer in rows
    ]

    return AdminPaymentListResponse(
        items=items,
        page=page,
        limit=limit,
        total=total,
    )