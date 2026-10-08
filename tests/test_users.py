
def register_user(
    client,
    email="user@example.com",
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
    email="user@example.com",
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


def create_authenticated_user(
    client,
    email="user@example.com",
    password="password123",
    first_name="Test",
    last_name="User",
    phone=None,
):
    register_response = register_user(
        client,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
    )

    assert register_response.status_code == 201

    login_response = login_user(
        client,
        email=email,
        password=password,
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return get_auth_headers(token)


def test_get_my_profile(client):
    headers = create_authenticated_user(client)

    response = client.get(
        "/users/me",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "user@example.com"
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"

    assert "password" not in data
    assert "password_hash" not in data


def test_get_my_profile_without_token(client):
    response = client.get("/users/me")

    assert response.status_code == 401


def test_update_first_name(client):
    headers = create_authenticated_user(client)

    response = client.patch(
        "/users/me",
        headers=headers,
        json={
            "first_name": "Updated",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["first_name"] == "Updated"
    assert data["last_name"] == "User"


def test_update_last_name(client):
    headers = create_authenticated_user(client)

    response = client.patch(
        "/users/me",
        headers=headers,
        json={
            "last_name": "Updated",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["first_name"] == "Test"
    assert data["last_name"] == "Updated"


def test_update_phone(client):
    headers = create_authenticated_user(client)

    response = client.patch(
        "/users/me",
        headers=headers,
        json={
            "phone": "09120000001",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["phone"] == "09120000001"


def test_update_multiple_fields(client):
    headers = create_authenticated_user(client)

    response = client.patch(
        "/users/me",
        headers=headers,
        json={
            "first_name": "NewFirst",
            "last_name": "NewLast",
            "phone": "09120000002",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["first_name"] == "NewFirst"
    assert data["last_name"] == "NewLast"
    assert data["phone"] == "09120000002"


def test_update_phone_duplicate(client):
    first_headers = create_authenticated_user(
        client,
        email="first@example.com",
        phone="09120000001",
    )

    second_headers = create_authenticated_user(
        client,
        email="second@example.com",
    )

    response = client.patch(
        "/users/me",
        headers=second_headers,
        json={
            "phone": "09120000001",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Phone already registered"


def test_remove_phone_not_allowed(client):
    headers = create_authenticated_user(
        client,
        phone="09120000001",
    )

    response = client.patch(
        "/users/me",
        headers=headers,
        json={
            "phone": None,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Phone cannot be removed"


def test_update_without_token(client):
    response = client.patch(
        "/users/me",
        json={
            "first_name": "Updated",
        },
    )

    assert response.status_code == 401


def test_email_cannot_be_changed(client):
    headers = create_authenticated_user(client)

    response = client.patch(
        "/users/me",
        headers=headers,
        json={
            "email": "new@example.com",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "user@example.com"


def test_role_cannot_be_changed(client):
    headers = create_authenticated_user(client)

    response = client.patch(
        "/users/me",
        headers=headers,
        json={
            "role": "admin",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["role"] == "customer"


def test_is_active_cannot_be_changed(client):
    headers = create_authenticated_user(client)

    response = client.patch(
        "/users/me",
        headers=headers,
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "is_active" not in data


def test_update_empty_body(client):
    headers = create_authenticated_user(client)

    response = client.patch(
        "/users/me",
        headers=headers,
        json={},
    )

    assert response.status_code == 200


def test_update_invalid_field_type(client):
    headers = create_authenticated_user(client)

    response = client.patch(
        "/users/me",
        headers=headers,
        json={
            "first_name": 123,
        },
    )

    assert response.status_code == 422
