from sqlalchemy import select
from sqlalchemy.orm import Session

from app.addresses.models import Address
from app.addresses.schemas import (
    AddressCreateRequest,
    AddressUpdateRequest,
)
from app.core.exceptions import AddressNotFoundError
from app.users.models import User


def get_user_addresses(
    db: Session,
    user: User,
) -> list[Address]:

    return list(
        db.scalars(
            select(Address)
            .where(
                Address.user_id == user.id
            )
            .order_by(Address.id)
        ).all()
    )


def get_user_address(
    db: Session,
    user: User,
    address_id: int,
) -> Address:

    address = db.scalar(
        select(Address).where(
            Address.id == address_id,
            Address.user_id == user.id,
        )
    )

    if address is None:
        raise AddressNotFoundError()

    return address


def create_address(
    db: Session,
    user: User,
    data: AddressCreateRequest,
) -> Address:

    has_address = db.scalar(
        select(Address.id)
        .where(
            Address.user_id == user.id
        )
        .limit(1)
    )

    address = Address(
        user_id=user.id,
        title=data.title,
        recipient_name=data.recipient_name,
        phone=data.phone,
        province=data.province,
        city=data.city,
        address_line=data.address_line,
        postal_code=data.postal_code,
        is_default=has_address is None,
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    return address


def update_address(
    db: Session,
    address: Address,
    data: AddressUpdateRequest,
) -> Address:

    update_data = data.model_dump(
        exclude_unset=True,
    )

    if "title" in update_data:
        address.title = update_data["title"]

    if "recipient_name" in update_data:
        address.recipient_name = update_data["recipient_name"]

    if "phone" in update_data:
        address.phone = update_data["phone"]

    if "province" in update_data:
        address.province = update_data["province"]

    if "city" in update_data:
        address.city = update_data["city"]

    if "address_line" in update_data:
        address.address_line = update_data["address_line"]

    if "postal_code" in update_data:
        address.postal_code = update_data["postal_code"]

    db.commit()
    db.refresh(address)

    return address


def set_default_address(
    db: Session,
    address: Address,
) -> Address:

    current_default = db.scalar(
        select(Address).where(
            Address.user_id == address.user_id,
            Address.is_default.is_(True),
        )
    )

    if current_default is not None:
        current_default.is_default = False
        db.flush()

    address.is_default = True

    db.commit()
    db.refresh(address)

    return address


def delete_address(
    db: Session,
    address: Address,
) -> None:

    user_id = address.user_id
    was_default = address.is_default

    db.delete(address)
    db.flush()

    if was_default:
        next_address = db.scalar(
            select(Address)
            .where(
                Address.user_id == user_id,
            )
            .order_by(Address.id)
            .limit(1)
        )

        if next_address is not None:
            next_address.is_default = True

    db.commit()