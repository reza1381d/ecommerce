from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.exceptions import InsufficientStockError
from app.products.models import Product


class InventoryService:

    @staticmethod
    def reserve(
        db: Session,
        product_id: int,
        quantity: int,
    ) -> None:
        result = db.execute(
            update(Product)
            .where(
                Product.id == product_id,
                Product.stock - Product.reserved_stock >= quantity,
            )
            .values(
                reserved_stock=Product.reserved_stock + quantity,
            )
        )

        if result.rowcount != 1:
            raise InsufficientStockError()

    @staticmethod
    def consume(
        db: Session,
        product_id: int,
        quantity: int,
    ) -> None:
        result = db.execute(
            update(Product)
            .where(
                Product.id == product_id,
                Product.reserved_stock >= quantity,
            )
            .values(
                stock=Product.stock - quantity,
                reserved_stock=Product.reserved_stock - quantity,
            )
        )

        if result.rowcount != 1:
            raise InsufficientStockError()

    @staticmethod
    def release(
        db: Session,
        product_id: int,
        quantity: int,
    ) -> None:
        result = db.execute(
            update(Product)
            .where(
                Product.id == product_id,
                Product.reserved_stock >= quantity,
            )
            .values(
                reserved_stock=Product.reserved_stock - quantity,
            )
        )

        if result.rowcount != 1:
            raise InsufficientStockError()