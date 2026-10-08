from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin, get_current_user_id
from app.coupons.schemas import (
    CouponCreateRequest,
    CouponResponse,
    CouponUpdateRequest,
    CouponValidationRequest,
    CouponValidationResponse,
)
from app.coupons.service import (
    create_coupon,
    get_coupon,
    get_coupon_by_code,
    update_coupon,
    preview_coupon_for_cart,
)
from app.core.database import get_db
from app.users.models import User


router = APIRouter(
    prefix="/coupons",
    tags=["Coupons"],
)


@router.post(
    "/validate",
    response_model=CouponValidationResponse,
)
def validate_for_cart(
    data: CouponValidationRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return preview_coupon_for_cart(
        db=db,
        code=data.code,
        user_id=user_id,
    )


@router.post(
    "",
    response_model=CouponResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: CouponCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return create_coupon(
        db=db,
        data=data,
    )


@router.get(
    "/code/{code}",
    response_model=CouponResponse,
)
def get_by_code(
    code: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return get_coupon_by_code(
        db=db,
        code=code,
    )


@router.get(
    "/{coupon_id}",
    response_model=CouponResponse,
)
def get(
    coupon_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return get_coupon(
        db=db,
        coupon_id=coupon_id,
    )


@router.patch(
    "/{coupon_id}",
    response_model=CouponResponse,
)
def update(
    coupon_id: int,
    data: CouponUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    coupon = get_coupon(
        db=db,
        coupon_id=coupon_id,
    )

    return update_coupon(
        db=db,
        coupon=coupon,
        data=data,
    )
