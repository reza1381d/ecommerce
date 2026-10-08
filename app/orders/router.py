from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user_id
from app.core.database import get_db
from app.orders.schemas import (
    CheckoutRequest,
    OrderAddressResponse,
    OrderItemResponse,
    OrderListResponse,
    OrderResponse,
)
from app.orders.service import (
    cancel_order as cancel_order_service,
    checkout,
    get_order,
    get_user_orders,
)


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


def build_order_response(
    order,
) -> OrderResponse:

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        subtotal=order.subtotal,
        discount_amount=order.discount_amount,
        shipping_amount=order.shipping_amount,
        tax_amount=order.tax_amount,
        total_amount=order.total_amount,
        address=OrderAddressResponse.model_validate(
            order.address
        ),
        items=[
            OrderItemResponse.model_validate(item)
            for item in order.items
        ],
    )


@router.post(
    "/checkout",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order_from_cart(
    data: CheckoutRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    order = checkout(
        db=db,
        user_id=user_id,
        address_id=data.address_id,
        coupon_code=data.coupon_code,
    )

    return build_order_response(
        order=order,
    )


@router.get(
    "",
    response_model=OrderListResponse,
)
def list_orders(
    page: int = Query(
        default=1,
        ge=1,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    orders, total = get_user_orders(
        db=db,
        user_id=user_id,
        page=page,
        limit=limit,
    )

    return OrderListResponse(
        items=[
            build_order_response(
                order=order,
            )
            for order in orders
        ],
        page=page,
        limit=limit,
        total=total,
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def get_order_by_id(
    order_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    order = get_order(
        db=db,
        user_id=user_id,
        order_id=order_id,
    )

    return build_order_response(
        order=order,
    )


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
)
def cancel_order(
    order_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    order = cancel_order_service(
        db=db,
        user_id=current_user_id,
        order_id=order_id,
    )

    return build_order_response(
        order=order,
    )
