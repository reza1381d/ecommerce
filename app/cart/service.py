from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cart.models import Cart, CartItem
from app.core.exceptions import (
    CartItemNotFoundError,
    InsufficientStockError,
    ProductInactiveError,
    ProductNotFoundError,
)
from app.products.models import Product
from app.users.models import User


def get_or_create_cart(
    db: Session,
    user: User,
) -> Cart:

    cart = db.scalar(
        select(Cart).where(
            Cart.user_id == user.id
        )
    )

    if cart is not None:
        return cart

    cart = Cart(
        user_id=user.id,
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    return cart


def add_cart_item(
    db: Session,
    cart: Cart,
    product_id: int,
    quantity: int,
) -> CartItem:

    product = db.scalar(
        select(Product).where(
            Product.id == product_id
        )
    )

    if product is None:
        raise ProductNotFoundError()

    if not product.is_active:
        raise ProductInactiveError()

    cart_item = db.scalar(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id,
        )
    )

    if cart_item is not None:
        new_quantity = cart_item.quantity + quantity

        if new_quantity > product.stock:
            raise InsufficientStockError()

        cart_item.quantity = new_quantity

    else:
        if quantity > product.stock:
            raise InsufficientStockError()

        cart_item = CartItem(
            cart_id=cart.id,
            product_id=product_id,
            quantity=quantity,
        )

        db.add(cart_item)

    db.commit()
    db.refresh(cart_item)

    return cart_item


def update_cart_item(
    db: Session,
    cart: Cart,
    item_id: int,
    quantity: int,
) -> CartItem:

    cart_item = db.scalar(
        select(CartItem).where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id,
        )
    )

    if cart_item is None:
        raise CartItemNotFoundError()

    product = db.scalar(
        select(Product).where(
            Product.id == cart_item.product_id
        )
    )

    if product is None:
        raise ProductNotFoundError()

    if not product.is_active:
        raise ProductInactiveError()

    if quantity > product.stock:
        raise InsufficientStockError()

    cart_item.quantity = quantity

    db.commit()
    db.refresh(cart_item)

    return cart_item


def remove_cart_item(
    db: Session,
    cart: Cart,
    item_id: int,
) -> None:

    cart_item = db.scalar(
        select(CartItem).where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id,
        )
    )

    if cart_item is None:
        raise CartItemNotFoundError()

    db.delete(cart_item)
    db.commit()