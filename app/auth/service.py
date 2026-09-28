from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.schemas import LoginRequest, RegisterRequest
from app.auth.security import hash_password, verify_password
from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
    PhoneAlreadyRegisteredError,
)
from app.users.models import User


def register_user(
    db: Session,
    data: RegisterRequest,
) -> User:

    existing_user = db.scalar(
        select(User).where(User.email == data.email)
    )

    if existing_user:
        raise EmailAlreadyRegisteredError()

    if data.phone is not None:
        existing_phone = db.scalar(
            select(User).where(User.phone == data.phone)
        )

        if existing_phone:
            raise PhoneAlreadyRegisteredError()

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise EmailAlreadyRegisteredError()

    db.refresh(user)

    return user


def login_user(
    db: Session,
    data: LoginRequest,
) -> User:

    user = db.scalar(
        select(User).where(User.email == data.email)
    )

    if not user:
        raise InvalidCredentialsError()

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise InvalidCredentialsError()

    if not user.is_active:
        raise InactiveUserError()

    return user