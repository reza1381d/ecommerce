from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.addresses.schemas import (
    AddressCreateRequest,
    AddressResponse,
    AddressUpdateRequest,
)
from app.addresses.service import (
    create_address,
    delete_address,
    get_user_address,
    get_user_addresses,
    set_default_address,
    update_address,
)
from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.users.models import User


router = APIRouter(
    prefix="/addresses",
    tags=["Addresses"],
)


@router.post(
    "",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: AddressCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_address(
        db=db,
        user=current_user,
        data=data,
    )


@router.get(
    "",
    response_model=list[AddressResponse],
)
def list_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_user_addresses(
        db=db,
        user=current_user,
    )


@router.get(
    "/{address_id}",
    response_model=AddressResponse,
)
def get(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_user_address(
        db=db,
        user=current_user,
        address_id=address_id,
    )


@router.patch(
    "/{address_id}",
    response_model=AddressResponse,
)
def update(
    address_id: int,
    data: AddressUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    address = get_user_address(
        db=db,
        user=current_user,
        address_id=address_id,
    )

    return update_address(
        db=db,
        address=address,
        data=data,
    )


@router.patch(
    "/{address_id}/default",
    response_model=AddressResponse,
)
def set_default(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    address = get_user_address(
        db=db,
        user=current_user,
        address_id=address_id,
    )

    return set_default_address(
        db=db,
        address=address,
    )


@router.delete(
    "/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    address = get_user_address(
        db=db,
        user=current_user,
        address_id=address_id,
    )

    delete_address(
        db=db,
        address=address,
    )