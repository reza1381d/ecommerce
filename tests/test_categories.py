from sqlalchemy import select

from app.users.models import User


def register_user(
    client,
    email="user@example.com",
    password="password123",
    first_name="Test",
    last_name="User",
):
    return client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
        },
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
):
    register_response = register_user(
        client,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
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


def create_admin(
    client,
    db,
    email="admin@example.com",
):
    headers = create_authenticated_user(
        client,
        email=email,
    )

    user = db.scalar(
        select(User).where(User.email == email)
    )

    assert user is not None

    user.role = "admin"
    db.commit()

    login_response = login_user(
        client,
        email=email,
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return get_auth_headers(token)


def test_get_categories_empty(client):
    response = client.get("/categories")

    assert response.status_code == 200
    assert response.json() == []


def test_create_category(client, db):
    headers = create_admin(
        client,
        db,
    )

    response = client.post(
        "/categories",
        headers=headers,
        json={
            "name": "Electronics",
            "description": "Electronic products",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Electronics"
    assert data["description"] == "Electronic products"
    assert data["is_active"] is True
    assert "id" in data


def test_get_category(client, db):
    headers = create_admin(
        client,
        db,
    )

    create_response = client.post(
        "/categories",
        headers=headers,
        json={
            "name": "Books",
            "description": "Books and publications",
        },
    )

    assert create_response.status_code == 201

    category_id = create_response.json()["id"]

    response = client.get(
        f"/categories/{category_id}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == category_id
    assert data["name"] == "Books"
    assert data["description"] == "Books and publications"


def test_get_nonexistent_category(client):
    response = client.get("/categories/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_get_categories(client, db):
    headers = create_admin(
        client,
        db,
    )

    first_response = client.post(
        "/categories",
        headers=headers,
        json={
            "name": "Category One",
        },
    )

    second_response = client.post(
        "/categories",
        headers=headers,
        json={
            "name": "Category Two",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.get("/categories")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] == "Category One"
    assert data[1]["name"] == "Category Two"


def test_create_category_without_authentication(client):
    response = client.post(
        "/categories",
        json={
            "name": "Electronics",
        },
    )

    assert response.status_code == 401


def test_create_category_as_customer(client):
    headers = create_authenticated_user(client)

    response = client.post(
        "/categories",
        headers=headers,
        json={
            "name": "Electronics",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_create_duplicate_category(client, db):
    headers = create_admin(
        client,
        db,
    )

    first_response = client.post(
        "/categories",
        headers=headers,
        json={
            "name": "Electronics",
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/categories",
        headers=headers,
        json={
            "name": "Electronics",
        },
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Category name already exists"


def test_update_category(client, db):
    headers = create_admin(
        client,
        db,
    )

    create_response = client.post(
        "/categories",
        headers=headers,
        json={
            "name": "Old Name",
            "description": "Old description",
        },
    )

    assert create_response.status_code == 201

    category_id = create_response.json()["id"]

    response = client.patch(
        f"/categories/{category_id}",
        headers=headers,
        json={
            "name": "New Name",
            "description": "New description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == category_id
    assert data["name"] == "New Name"
    assert data["description"] == "New description"


def test_update_category_as_customer(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_response = client.post(
        "/categories",
        headers=admin_headers,
        json={
            "name": "Electronics",
        },
    )

    assert create_response.status_code == 201

    category_id = create_response.json()["id"]

    customer_headers = create_authenticated_user(
        client,
        email="customer@example.com",
    )

    response = client.patch(
        f"/categories/{category_id}",
        headers=customer_headers,
        json={
            "name": "Updated",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_update_nonexistent_category(client, db):
    headers = create_admin(
        client,
        db,
    )

    response = client.patch(
        "/categories/999999",
        headers=headers,
        json={
            "name": "Updated",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_update_duplicate_category_name(client, db):
    headers = create_admin(
        client,
        db,
    )

    first_response = client.post(
        "/categories",
        headers=headers,
        json={
            "name": "Electronics",
        },
    )

    second_response = client.post(
        "/categories",
        headers=headers,
        json={
            "name": "Books",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    second_category_id = second_response.json()["id"]

    response = client.patch(
        f"/categories/{second_category_id}",
        headers=headers,
        json={
            "name": "Electronics",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Category name already exists"


def test_update_category_is_active(client, db):
    headers = create_admin(
        client,
        db,
    )

    create_response = client.post(
        "/categories",
        headers=headers,
        json={
            "name": "Electronics",
        },
    )

    assert create_response.status_code == 201

    category_id = create_response.json()["id"]

    response = client.patch(
        f"/categories/{category_id}",
        headers=headers,
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_delete_category(client, db):
    headers = create_admin(
        client,
        db,
    )

    create_response = client.post(
        "/categories",
        headers=headers,
        json={
            "name": "Electronics",
        },
    )

    assert create_response.status_code == 201

    category_id = create_response.json()["id"]

    response = client.delete(
        f"/categories/{category_id}",
        headers=headers,
    )

    assert response.status_code == 204


def test_delete_category_as_customer(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_response = client.post(
        "/categories",
        headers=admin_headers,
        json={
            "name": "Electronics",
        },
    )

    assert create_response.status_code == 201

    category_id = create_response.json()["id"]

    customer_headers = create_authenticated_user(
        client,
        email="customer@example.com",
    )

    response = client.delete(
        f"/categories/{category_id}",
        headers=customer_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_delete_nonexistent_category(client, db):
    headers = create_admin(
        client,
        db,
    )

    response = client.delete(
        "/categories/999999",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_delete_category_is_soft_delete(client, db):
    headers = create_admin(
        client,
        db,
    )

    create_response = client.post(
        "/categories",
        headers=headers,
        json={
            "name": "Electronics",
        },
    )

    assert create_response.status_code == 201

    category_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/categories/{category_id}",
        headers=headers,
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/categories/{category_id}",
    )

    assert get_response.status_code == 200

    data = get_response.json()

    assert data["id"] == category_id
    assert data["name"] == "Electronics"
    assert data["is_active"] is False


def test_create_category_invalid_data(client, db):
    headers = create_admin(
        client,
        db,
    )

    response = client.post(
        "/categories",
        headers=headers,
        json={},
    )

    assert response.status_code == 422


def test_update_category_invalid_data(client, db):
    headers = create_admin(
        client,
        db,
    )

    create_response = client.post(
        "/categories",
        headers=headers,
        json={
            "name": "Electronics",
        },
    )

    assert create_response.status_code == 201

    category_id = create_response.json()["id"]

    response = client.patch(
        f"/categories/{category_id}",
        headers=headers,
        json={
            "is_active": "not-a-boolean",
        },
    )

    assert response.status_code == 422