from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.categories.models import Category
from app.core.exceptions import (
    CategoryAlreadyExistsError,
    CategoryInactiveError,
    CategoryNotFoundError,
    ProductNotFoundError,
    StockBelowReservedError,
)
from app.products.models import Product
from app.products.schemas import (
    ProductCreateRequest,
    ProductUpdateRequest,
)


def _validate_category(
    db: Session,
    category_id: int | None,
) -> None:

    if category_id is None:
        return

    category = db.scalar(
        select(Category).where(
            Category.id == category_id
        )
    )

    if category is None:
        raise CategoryNotFoundError()

    if not category.is_active:
        raise CategoryInactiveError()


def create_product(
    db: Session,
    data: ProductCreateRequest,
) -> Product:

    _validate_category(
        db=db,
        category_id=data.category_id,
    )

    product = Product(
        name=data.name,
        description=data.description,
        price=data.price,
        stock=data.stock,
        category_id=data.category_id,
    )

    db.add(product)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    db.refresh(product)

    return product


def get_products(
    db: Session,
    page: int,
    limit: int,
    search: str | None = None,
    category_id: int | None = None,
    is_active: bool | None = None,
    sort_by: str = "id",
    sort_order: str = "asc",
) -> tuple[list[Product], int]:

    filters = []

    if search is not None:
        search_pattern = f"%{search}%"

        filters.append(
            Product.name.ilike(search_pattern)
        )

    if category_id is not None:
        filters.append(
            Product.category_id == category_id
        )

    if is_active is not None:
        filters.append(
            Product.is_active == is_active
        )

    sort_columns = {
        "id": Product.id,
        "name": Product.name,
        "price": Product.price,
        "created_at": Product.created_at,
    }

    sort_column = sort_columns[sort_by]

    if sort_order == "desc":
        order_expression = sort_column.desc()
    else:
        order_expression = sort_column.asc()

    offset = (page - 1) * limit

    products = list(
        db.scalars(
            select(Product)
            .where(*filters)
            .order_by(order_expression)
            .offset(offset)
            .limit(limit)
        ).all()
    )

    total = db.scalar(
        select(func.count())
        .select_from(Product)
        .where(*filters)
    )

    return products, total


def get_product(
    db: Session,
    product_id: int,
) -> Product:

    product = db.scalar(
        select(Product).where(
            Product.id == product_id
        )
    )

    if product is None:
        raise ProductNotFoundError()

    return product


def update_product(
    db: Session,
    product: Product,
    data: ProductUpdateRequest,
) -> Product:

    update_data = data.model_dump(
        exclude_unset=True,
    )

    if "category_id" in update_data:
        _validate_category(
            db=db,
            category_id=update_data["category_id"],
        )

        product.category_id = update_data["category_id"]

    if "name" in update_data:
        product.name = update_data["name"]

    if "description" in update_data:
        product.description = update_data["description"]

    if "price" in update_data:
        product.price = update_data["price"]

    if "stock" in update_data:
        if update_data["stock"] < product.reserved_stock:
            raise StockBelowReservedError()

        product.stock = update_data["stock"]

    if "is_active" in update_data:
        product.is_active = update_data["is_active"]

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    db.refresh(product)

    return product


def delete_product(
    db: Session,
    product: Product,
) -> None:

    product.is_active = False

    db.commit()