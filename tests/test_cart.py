from sqlalchemy import select

from app.cart.models import Cart, CartItem
from app.products.models import Product
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
):
    register_response = register_user(
        client,
        email=email,
    )

    assert register_response.status_code == 201

    login_response = login_user(
        client,
        email=email,
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return get_auth_headers(token)


def create_admin(
    client,
    db,
    email="admin@example.com",
):
    create_authenticated_user(
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


def create_product(
    client,
    admin_headers,
    name="Laptop",
    price="1000.00",
    stock=10,
):
    return client.post(
        "/products",
        headers=admin_headers,
        json={
            "name": name,
            "price": price,
            "stock": stock,
        },
    )


def test_get_cart_requires_authentication(client):
    response = client.get("/cart")

    assert response.status_code == 401


def test_get_cart_creates_empty_cart(client):
    headers = create_authenticated_user(client)

    response = client.get(
        "/cart",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert "id" in data
    assert data["user_id"] > 0
    assert data["items"] == []


def test_get_cart_returns_same_cart(client):
    headers = create_authenticated_user(client)

    first_response = client.get(
        "/cart",
        headers=headers,
    )

    assert first_response.status_code == 200

    first_data = first_response.json()

    second_response = client.get(
        "/cart",
        headers=headers,
    )

    assert second_response.status_code == 200

    second_data = second_response.json()

    assert second_data["id"] == first_data["id"]
    assert second_data["user_id"] == first_data["user_id"]


def test_add_cart_item(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    product_response = create_product(
        client,
        admin_headers,
    )

    assert product_response.status_code == 201

    product_id = product_response.json()["id"]

    user_headers = create_authenticated_user(
        client,
        email="customer@example.com",
    )

    response = client.post(
        "/cart/items",
        headers=user_headers,
        json={
            "product_id": product_id,
            "quantity": 2,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["product_id"] == product_id
    assert data["quantity"] == 2
    assert "id" in data


def test_add_cart_item_updates_existing_item_quantity(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    product_response = create_product(
        client,
        admin_headers,
        stock=10,
    )

    assert product_response.status_code == 201

    product_id = product_response.json()["id"]

    user_headers = create_authenticated_user(
        client,
        email="customer@example.com",
    )

    first_response = client.post(
        "/cart/items",
        headers=user_headers,
        json={
            "product_id": product_id,
            "quantity": 2,
        },
    )

    assert first_response.status_code == 201

    item_id = first_response.json()["id"]

    second_response = client.post(
        "/cart/items",
        headers=user_headers,
        json={
            "product_id": product_id,
            "quantity": 3,
        },
    )

    assert second_response.status_code == 201

    data = second_response.json()

    assert data["id"] == item_id
    assert data["product_id"] == product_id
    assert data["quantity"] == 5


def test_add_cart_item_product_not_found(client):
    headers = create_authenticated_user(client)

    response = client.post(
        "/cart/items",
        headers=headers,
        json={
            "product_id": 999999,
            "quantity": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_add_inactive_product_to_cart(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    product_response = create_product(
        client,
        admin_headers,
    )

    assert product_response.status_code == 201

    product_id = product_response.json()["id"]

    delete_response = client.delete(
        f"/products/{product_id}",
        headers=admin_headers,
    )

    assert delete_response.status_code == 204

    user_headers = create_authenticated_user(
        client,
        email="customer@example.com",
    )

    response = client.post(
        "/cart/items",
        headers=user_headers,
        json={
            "product_id": product_id,
            "quantity": 1,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Product is inactive"


def test_add_cart_item_insufficient_stock(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    product_response = create_product(
        client,
        admin_headers,
        stock=5,
    )

    assert product_response.status_code == 201

    product_id = product_response.json()["id"]

    user_headers = create_authenticated_user(
        client,
        email="customer@example.com",
    )

    response = client.post(
        "/cart/items",
        headers=user_headers,
        json={
            "product_id": product_id,
            "quantity": 6,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Insufficient stock"


def test_add_cart_item_exceeding_stock_after_existing_quantity(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    product_response = create_product(
        client,
        admin_headers,
        stock=5,
    )

    assert product_response.status_code == 201

    product_id = product_response.json()["id"]

    user_headers = create_authenticated_user(
        client,
        email="customer@example.com",
    )

    first_response = client.post(
        "/cart/items",
        headers=user_headers,
        json={
            "product_id": product_id,
            "quantity": 3,
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/cart/items",
        headers=user_headers,
        json={
            "product_id": product_id,
            "quantity": 3,
        },
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Insufficient stock"


def test_update_cart_item(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    product_response = create_product(
        client,
        admin_headers,
        stock=10,
    )

    assert product_response.status_code == 201

    product_id = product_response.json()["id"]

    user_headers = create_authenticated_user(
        client,
        email="customer@example.com",
    )

    create_response = client.post(
        "/cart/items",
        headers=user_headers,
        json={
            "product_id": product_id,
            "quantity": 2,
        },
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["id"]

    response = client.patch(
        f"/cart/items/{item_id}",
        headers=user_headers,
        json={
            "quantity": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == item_id
    assert data["product_id"] == product_id
    assert data["quantity"] == 5


def test_update_cart_item_insufficient_stock(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    product_response = create_product(
        client,
        admin_headers,
        stock=5,
    )

    assert product_response.status_code == 201

    product_id = product_response.json()["id"]

    user_headers = create_authenticated_user(
        client,
        email="customer@example.com",
    )

    create_response = client.post(
        "/cart/items",
        headers=user_headers,
        json={
            "product_id": product_id,
            "quantity": 2,
        },
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["id"]

    response = client.patch(
        f"/cart/items/{item_id}",
        headers=user_headers,
        json={
            "quantity": 6,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Insufficient stock"


def test_update_nonexistent_cart_item(client):
    headers = create_authenticated_user(client)

    response = client.patch(
        "/cart/items/999999",
        headers=headers,
        json={
            "quantity": 2,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Cart item not found"


def test_remove_cart_item(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    product_response = create_product(
        client,
        admin_headers,
    )

    assert product_response.status_code == 201

    product_id = product_response.json()["id"]

    user_headers = create_authenticated_user(
        client,
        email="customer@example.com",
    )

    create_response = client.post(
        "/cart/items",
        headers=user_headers,
        json={
            "product_id": product_id,
            "quantity": 2,
        },
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["id"]

    response = client.delete(
        f"/cart/items/{item_id}",
        headers=user_headers,
    )

    assert response.status_code == 204


def test_remove_nonexistent_cart_item(client):
    headers = create_authenticated_user(client)

    response = client.delete(
        "/cart/items/999999",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Cart item not found"


def test_user_cannot_modify_another_users_cart_item(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    product_response = create_product(
        client,
        admin_headers,
    )

    assert product_response.status_code == 201

    product_id = product_response.json()["id"]

    first_user_headers = create_authenticated_user(
        client,
        email="first@example.com",
    )

    create_response = client.post(
        "/cart/items",
        headers=first_user_headers,
        json={
            "product_id": product_id,
            "quantity": 2,
        },
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["id"]

    second_user_headers = create_authenticated_user(
        client,
        email="second@example.com",
    )

    update_response = client.patch(
        f"/cart/items/{item_id}",
        headers=second_user_headers,
        json={
            "quantity": 5,
        },
    )

    assert update_response.status_code == 404
    assert update_response.json()["detail"] == "Cart item not found"

    delete_response = client.delete(
        f"/cart/items/{item_id}",
        headers=second_user_headers,
    )

    assert delete_response.status_code == 404
    assert delete_response.json()["detail"] == "Cart item not found"


def test_cart_item_quantity_must_be_positive(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    product_response = create_product(
        client,
        admin_headers,
    )

    assert product_response.status_code == 201

    product_id = product_response.json()["id"]

    user_headers = create_authenticated_user(
        client,
        email="customer@example.com",
    )

    response = client.post(
        "/cart/items",
        headers=user_headers,
        json={
            "product_id": product_id,
            "quantity": 0,
        },
    )

    assert response.status_code == 422


def test_cart_item_product_id_must_be_positive(client):
    headers = create_authenticated_user(client)

    response = client.post(
        "/cart/items",
        headers=headers,
        json={
            "product_id": 0,
            "quantity": 1,
        },
    )

    assert response.status_code == 422


def test_update_cart_item_quantity_must_be_positive(client):
    headers = create_authenticated_user(client)

    response = client.patch(
        "/cart/items/999999",
        headers=headers,
        json={
            "quantity": 0,
        },
    )

    assert response.status_code == 422


def test_cart_items_belong_to_correct_cart(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    product_response = create_product(
        client,
        admin_headers,
    )

    assert product_response.status_code == 201

    product_id = product_response.json()["id"]

    first_user_headers = create_authenticated_user(
        client,
        email="first@example.com",
    )

    create_response = client.post(
        "/cart/items",
        headers=first_user_headers,
        json={
            "product_id": product_id,
            "quantity": 2,
        },
    )

    assert create_response.status_code == 201

    first_cart = db.scalar(
        select(Cart).join(User).where(
            User.email == "first@example.com"
        )
    )

    assert first_cart is not None

    item = db.scalar(
        select(CartItem).where(
            CartItem.cart_id == first_cart.id,
            CartItem.product_id == product_id,
        )
    )

    assert item is not None
    assert item.quantity == 2

    second_user_headers = create_authenticated_user(
        client,
        email="second@example.com",
    )

    second_cart_response = client.get(
        "/cart",
        headers=second_user_headers,
    )

    assert second_cart_response.status_code == 200

    second_cart_data = second_cart_response.json()

    assert second_cart_data["id"] != first_cart.id
    assert second_cart_data["items"] == []