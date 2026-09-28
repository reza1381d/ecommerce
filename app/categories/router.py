from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.categories.schemas import (
    CategoryCreateRequest,
    CategoryResponse,
    CategoryUpdateRequest,
)
from app.categories.service import (
    create_category,
    delete_category,
    get_categories,
    get_category,
    update_category,
)
from app.core.database import get_db
from app.users.models import User


router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: CategoryCreateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return create_category(
        db=db,
        data=data,
    )


@router.get(
    "",
    response_model=list[CategoryResponse],
)
def list_all(
    db: Session = Depends(get_db),
):
    return get_categories(
        db=db,
    )


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
)
def get(
    category_id: int,
    db: Session = Depends(get_db),
):
    return get_category(
        db=db,
        category_id=category_id,
    )


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
)
def update(
    category_id: int,
    data: CategoryUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    category = get_category(
        db=db,
        category_id=category_id,
    )

    return update_category(
        db=db,
        category=category,
        data=data,
    )


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    category_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    category = get_category(
        db=db,
        category_id=category_id,
    )

    delete_category(
        db=db,
        category=category,
    )