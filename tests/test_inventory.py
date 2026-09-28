from decimal import Decimal

import pytest

from app.core.exceptions import InsufficientStockError
from app.inventory.service import InventoryService
from app.products.models import Product


def create_product(
    db,
    *,
    stock: int,
    reserved_stock: int = 0,
) -> Product:
    product = Product(
        name="Test Product",
        description="Test description",
        price=Decimal("100.00"),
        stock=stock,
        reserved_stock=reserved_stock,
        is_active=True,
    )
    db.add(product)
    db.flush()
    return product


def test_reserve_increases_reserved_stock(db):
    product = create_product(db, stock=10)

    InventoryService.reserve(
        db=db,
        product_id=product.id,
        quantity=3,
    )

    db.refresh(product)

    assert product.stock == 10
    assert product.reserved_stock == 3


def test_reserve_fails_when_available_stock_is_insufficient(db):
    product = create_product(
        db,
        stock=10,
        reserved_stock=8,
    )

    with pytest.raises(InsufficientStockError):
        InventoryService.reserve(
            db=db,
            product_id=product.id,
            quantity=3,
        )

    db.refresh(product)

    assert product.stock == 10
    assert product.reserved_stock == 8


def test_consume_decreases_stock_and_reserved_stock(db):
    product = create_product(
        db,
        stock=10,
        reserved_stock=3,
    )

    InventoryService.consume(
        db=db,
        product_id=product.id,
        quantity=3,
    )

    db.refresh(product)

    assert product.stock == 7
    assert product.reserved_stock == 0


def test_consume_fails_when_reserved_stock_is_insufficient(db):
    product = create_product(
        db,
        stock=10,
        reserved_stock=2,
    )

    with pytest.raises(InsufficientStockError):
        InventoryService.consume(
            db=db,
            product_id=product.id,
            quantity=3,
        )

    db.refresh(product)

    assert product.stock == 10
    assert product.reserved_stock == 2


def test_release_decreases_reserved_stock(db):
    product = create_product(
        db,
        stock=10,
        reserved_stock=3,
    )

    InventoryService.release(
        db=db,
        product_id=product.id,
        quantity=3,
    )

    db.refresh(product)

    assert product.stock == 10
    assert product.reserved_stock == 0


def test_release_fails_when_reserved_stock_is_insufficient(db):
    product = create_product(
        db,
        stock=10,
        reserved_stock=2,
    )

    with pytest.raises(InsufficientStockError):
        InventoryService.release(
            db=db,
            product_id=product.id,
            quantity=3,
        )

    db.refresh(product)

    assert product.stock == 10
    assert product.reserved_stock == 2