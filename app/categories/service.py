from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.categories.models import Category
from app.categories.schemas import (
    CategoryCreateRequest,
    CategoryUpdateRequest,
)
from app.core.exceptions import (
    CategoryAlreadyExistsError,
    CategoryNotFoundError,
)


def create_category(
    db: Session,
    data: CategoryCreateRequest,
) -> Category:

    existing_category = db.scalar(
        select(Category).where(
            Category.name == data.name
        )
    )

    if existing_category:
        raise CategoryAlreadyExistsError()

    category = Category(
        name=data.name,
        description=data.description,
    )

    db.add(category)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise CategoryAlreadyExistsError()

    db.refresh(category)

    return category


def get_categories(
    db: Session,
) -> list[Category]:

    return list(
        db.scalars(
            select(Category).order_by(Category.id)
        ).all()
    )


def get_category(
    db: Session,
    category_id: int,
) -> Category:

    category = db.scalar(
        select(Category).where(
            Category.id == category_id
        )
    )

    if category is None:
        raise CategoryNotFoundError()

    return category


def update_category(
    db: Session,
    category: Category,
    data: CategoryUpdateRequest,
) -> Category:

    update_data = data.model_dump(
        exclude_unset=True,
    )

    if "name" in update_data:
        existing_category = db.scalar(
            select(Category).where(
                Category.name == update_data["name"],
                Category.id != category.id,
            )
        )

        if existing_category:
            raise CategoryAlreadyExistsError()

        category.name = update_data["name"]

    if "description" in update_data:
        category.description = update_data["description"]

    if "is_active" in update_data:
        category.is_active = update_data["is_active"]

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise CategoryAlreadyExistsError()

    db.refresh(category)

    return category


def delete_category(
    db: Session,
    category: Category,
) -> None:

    category.is_active = False

    db.commit()