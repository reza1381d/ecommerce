from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.cart.schemas import (
    CartItemCreateRequest,
    CartItemResponse,
    CartItemUpdateRequest,
    CartResponse,
)
from app.cart.service import (
    add_cart_item,
    get_or_create_cart,
    remove_cart_item,
    update_cart_item,
)
from app.core.database import get_db
from app.users.models import User


router = APIRouter(
    prefix="/cart",
    tags=["Cart"],
)


@router.get(
    "",
    response_model=CartResponse,
)
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_or_create_cart(
        db=db,
        user=current_user,
    )


@router.post(
    "/items",
    response_model=CartItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_item(
    data: CartItemCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = get_or_create_cart(
        db=db,
        user=current_user,
    )

    return add_cart_item(
        db=db,
        cart=cart,
        product_id=data.product_id,
        quantity=data.quantity,
    )


@router.patch(
    "/items/{item_id}",
    response_model=CartItemResponse,
)
def update_item(
    item_id: int,
    data: CartItemUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = get_or_create_cart(
        db=db,
        user=current_user,
    )

    return update_cart_item(
        db=db,
        cart=cart,
        item_id=item_id,
        quantity=data.quantity,
    )


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = get_or_create_cart(
        db=db,
        user=current_user,
    )

    remove_cart_item(
        db=db,
        cart=cart,
        item_id=item_id,
    )