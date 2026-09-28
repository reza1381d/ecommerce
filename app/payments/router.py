from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.payments.schemas import (
    PaymentCreateRequest,
    PaymentResponse,
)
from app.payments.service import (
    create_payment,
    get_payment,
    get_user_payments,
)
from app.users.models import User


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=201,
)
def pay_order(
    data: PaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_payment(
        db=db,
        user=current_user,
        order_id=data.order_id,
    )


@router.get(
    "",
    response_model=list[PaymentResponse],
)
def list_my_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_user_payments(
        db=db,
        user=current_user,
    )


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
)
def get_payment_by_id(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_payment(
        db=db,
        user=current_user,
        payment_id=payment_id,
    )