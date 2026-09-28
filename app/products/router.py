from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.core.database import get_db
from app.products.schemas import (
    ProductCreateRequest,
    ProductListResponse,
    ProductResponse,
    ProductUpdateRequest,
)
from app.products.service import (
    create_product,
    delete_product,
    get_product,
    get_products,
    update_product,
)
from app.users.models import User


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: ProductCreateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return create_product(
        db=db,
        data=data,
    )


@router.get(
    "",
    response_model=ProductListResponse,
)
def list_products(
    page: int = Query(
        default=1,
        ge=1,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
    ),
    category_id: int | None = Query(
        default=None,
        gt=0,
    ),
    is_active: bool | None = Query(
        default=None,
    ),
    sort_by: Literal[
        "id",
        "name",
        "price",
        "created_at",
    ] = Query(
        default="id",
    ),
    sort_order: Literal[
        "asc",
        "desc",
    ] = Query(
        default="asc",
    ),
    db: Session = Depends(get_db),
):
    products, total = get_products(
        db=db,
        page=page,
        limit=limit,
        search=search,
        category_id=category_id,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return ProductListResponse(
        items=products,
        page=page,
        limit=limit,
        total=total,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get(
    product_id: int,
    db: Session = Depends(get_db),
):
    return get_product(
        db=db,
        product_id=product_id,
    )


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
)
def update(
    product_id: int,
    data: ProductUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    product = get_product(
        db=db,
        product_id=product_id,
    )

    return update_product(
        db=db,
        product=product,
        data=data,
    )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    product = get_product(
        db=db,
        product_id=product_id,
    )

    delete_product(
        db=db,
        product=product,
    )