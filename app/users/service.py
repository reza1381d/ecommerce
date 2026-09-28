from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    PhoneRemovalNotAllowedError,
    PhoneUpdateConflictError,
)
from app.users.models import User
from app.users.schemas import UserUpdateRequest


def update_user(
    db: Session,
    user: User,
    data: UserUpdateRequest,
) -> User:

    update_data = data.model_dump(
        exclude_unset=True,
    )

    if "first_name" in update_data:
        user.first_name = update_data["first_name"]

    if "last_name" in update_data:
        user.last_name = update_data["last_name"]

    if "phone" in update_data:
        if update_data["phone"] is None:
            raise PhoneRemovalNotAllowedError()

        existing_phone = db.scalar(
            select(User).where(
                User.phone == update_data["phone"],
                User.id != user.id,
            )
        )

        if existing_phone:
            raise PhoneUpdateConflictError()

        user.phone = update_data["phone"]

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise PhoneUpdateConflictError()

    db.refresh(user)

    return user