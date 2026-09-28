
from datetime import datetime, timedelta, timezone

import jwt


def register_user(
    client,
    email="test@example.com",
    password="password123",
    first_name="Test",
    last_name="User",
    phone=None,
):
    data = {
        "email": email,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
    }

    if phone is not None:
        data["phone"] = phone

    return client.post(
        "/auth/register",
        json=data,
    )


def login_user(
    client,
    email="test@example.com",
    password="password123",
):
    return client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def get_auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def test_register_user(client):
    response = register_user(client)

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "test@example.com"
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"

    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email(client):
    first_response = register_user(client)

    assert first_response.status_code == 201

    second_response = register_user(client)

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Email already registered"


def test_register_duplicate_phone(client):
    first_response = register_user(
        client,
        email="first@example.com",
        phone="09120000001",
    )

    assert first_response.status_code == 201

    second_response = register_user(
        client,
        email="second@example.com",
        phone="09120000001",
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Phone already registered"


def test_register_role_cannot_be_set_by_client(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "admin@example.com",
            "password": "password123",
            "first_name": "Admin",
            "last_name": "Attempt",
            "role": "admin",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert "role" not in data


def test_register_invalid_email(client):
    response = register_user(
        client,
        email="not-an-email",
    )

    assert response.status_code == 422


def test_register_missing_required_field(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "first_name": "Test",
        },
    )

    assert response.status_code == 422


def test_login_success(client):
    register_response = register_user(client)

    assert register_response.status_code == 201

    response = login_user(client)

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    register_response = register_user(client)

    assert register_response.status_code == 201

    response = login_user(
        client,
        password="wrong-password",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_nonexistent_user(client):
    response = login_user(
        client,
        email="does-not-exist@example.com",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_auth_me_without_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_auth_me_with_valid_token(client):
    register_response = register_user(client)

    assert register_response.status_code == 201

    login_response = login_user(client)

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers=get_auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "test@example.com"
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"


def test_auth_me_with_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers=get_auth_headers("this-is-not-a-valid-token"),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_auth_me_with_expired_token(client):
    register_response = register_user(client)

    assert register_response.status_code == 201

    user_id = register_response.json()["id"]

    from app.core.config import settings

    expired_token = jwt.encode(
        {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = client.get(
        "/auth/me",
        headers=get_auth_headers(expired_token),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_login_inactive_user(client, db):
    register_response = register_user(client)

    assert register_response.status_code == 201

    user_id = register_response.json()["id"]

    from sqlalchemy import select

    from app.users.models import User

    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    assert user is not None

    user.is_active = False
    db.commit()

    response = login_user(client)

    assert response.status_code == 401
    assert response.json()["detail"] == "User is inactive"


def test_auth_me_with_inactive_user(client, db):
    register_response = register_user(client)

    assert register_response.status_code == 201

    user_id = register_response.json()["id"]

    login_response = login_user(client)

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    from sqlalchemy import select

    from app.users.models import User

    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    assert user is not None

    user.is_active = False
    db.commit()

    response = client.get(
        "/auth/me",
        headers=get_auth_headers(token),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "User is inactive"
