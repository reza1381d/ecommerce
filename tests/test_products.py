from sqlalchemy import select

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


def create_category(
    client,
    admin_headers,
    name="Electronics",
    description="Electronic products",
):
    return client.post(
        "/categories",
        headers=admin_headers,
        json={
            "name": name,
            "description": description,
        },
    )


def create_product(
    client,
    admin_headers,
    name="Laptop",
    description="A laptop",
    price="1000.00",
    stock=10,
    category_id=None,
):
    data = {
        "name": name,
        "description": description,
        "price": price,
        "stock": stock,
    }

    if category_id is not None:
        data["category_id"] = category_id

    return client.post(
        "/products",
        headers=admin_headers,
        json=data,
    )


def test_get_products_empty(client):
    response = client.get("/products")

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["page"] == 1
    assert data["limit"] == 20
    assert data["total"] == 0


def test_create_product(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    response = create_product(
        client,
        admin_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Laptop"
    assert data["description"] == "A laptop"
    assert data["price"] == "1000"
    assert data["stock"] == 10
    assert data["reserved_stock"] == 0
    assert data["category_id"] is None
    assert data["is_active"] is True
    assert "id" in data


def test_create_product_with_category(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    category_response = create_category(
        client,
        admin_headers,
    )

    assert category_response.status_code == 201

    category_id = category_response.json()["id"]

    response = create_product(
        client,
        admin_headers,
        category_id=category_id,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["category_id"] == category_id


def test_get_product(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_response = create_product(
        client,
        admin_headers,
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    response = client.get(
        f"/products/{product_id}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == product_id
    assert data["name"] == "Laptop"
    assert data["price"] == "1000"
    assert data["stock"] == 10


def test_get_nonexistent_product(client):
    response = client.get("/products/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_get_products(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    first_response = create_product(
        client,
        admin_headers,
        name="Laptop",
    )

    second_response = create_product(
        client,
        admin_headers,
        name="Phone",
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.get("/products")

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) == 2
    assert data["items"][0]["name"] == "Laptop"
    assert data["items"][1]["name"] == "Phone"
    assert data["page"] == 1
    assert data["limit"] == 20
    assert data["total"] == 2


def test_get_products_page_one(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    for name in ["Laptop", "Phone", "Tablet"]:
        response = create_product(
            client,
            admin_headers,
            name=name,
        )

        assert response.status_code == 201

    response = client.get(
        "/products?page=1&limit=2"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["total"] == 3

    assert len(data["items"]) == 2
    assert data["items"][0]["name"] == "Laptop"
    assert data["items"][1]["name"] == "Phone"


def test_get_products_page_two(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    for name in ["Laptop", "Phone", "Tablet"]:
        response = create_product(
            client,
            admin_headers,
            name=name,
        )

        assert response.status_code == 201

    response = client.get(
        "/products?page=2&limit=2"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 2
    assert data["limit"] == 2
    assert data["total"] == 3

    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Tablet"


def test_get_products_empty_page(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    for name in ["Laptop", "Phone"]:
        response = create_product(
            client,
            admin_headers,
            name=name,
        )

        assert response.status_code == 201

    response = client.get(
        "/products?page=3&limit=2"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 3
    assert data["limit"] == 2
    assert data["total"] == 2
    assert data["items"] == []


def test_get_products_invalid_page(client):
    response = client.get(
        "/products?page=0"
    )

    assert response.status_code == 422


def test_get_products_invalid_limit_zero(client):
    response = client.get(
        "/products?limit=0"
    )

    assert response.status_code == 422


def test_get_products_invalid_limit_too_large(client):
    response = client.get(
        "/products?limit=101"
    )

    assert response.status_code == 422


def test_get_products_custom_limit(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    for name in ["Laptop", "Phone", "Tablet"]:
        response = create_product(
            client,
            admin_headers,
            name=name,
        )

        assert response.status_code == 201

    response = client.get(
        "/products?limit=1"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 1
    assert data["total"] == 3
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Laptop"


def test_create_product_without_authentication(client):
    response = client.post(
        "/products",
        json={
            "name": "Laptop",
            "price": "1000.00",
            "stock": 10,
        },
    )

    assert response.status_code == 401


def test_create_product_as_customer(client):
    headers = create_authenticated_user(client)

    response = create_product(
        client,
        headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_update_product(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_response = create_product(
        client,
        admin_headers,
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    response = client.patch(
        f"/products/{product_id}",
        headers=admin_headers,
        json={
            "name": "Gaming Laptop",
            "description": "Updated description",
            "price": "1500.00",
            "stock": 20,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == product_id
    assert data["name"] == "Gaming Laptop"
    assert data["description"] == "Updated description"
    assert data["price"] == "1500"
    assert data["stock"] == 20


def test_update_product_as_customer(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_response = create_product(
        client,
        admin_headers,
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    customer_headers = create_authenticated_user(
        client,
        email="customer@example.com",
    )

    response = client.patch(
        f"/products/{product_id}",
        headers=customer_headers,
        json={
            "name": "Updated",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_update_nonexistent_product(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    response = client.patch(
        "/products/999999",
        headers=admin_headers,
        json={
            "name": "Updated",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_update_product_category(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    first_category_response = create_category(
        client,
        admin_headers,
        name="Electronics",
    )

    second_category_response = create_category(
        client,
        admin_headers,
        name="Computers",
    )

    assert first_category_response.status_code == 201
    assert second_category_response.status_code == 201

    first_category_id = first_category_response.json()["id"]
    second_category_id = second_category_response.json()["id"]

    create_response = create_product(
        client,
        admin_headers,
        category_id=first_category_id,
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    response = client.patch(
        f"/products/{product_id}",
        headers=admin_headers,
        json={
            "category_id": second_category_id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["category_id"] == second_category_id


def test_create_product_with_nonexistent_category(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    response = create_product(
        client,
        admin_headers,
        category_id=999999,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_update_product_with_nonexistent_category(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_response = create_product(
        client,
        admin_headers,
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    response = client.patch(
        f"/products/{product_id}",
        headers=admin_headers,
        json={
            "category_id": 999999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_create_product_with_inactive_category(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    category_response = create_category(
        client,
        admin_headers,
    )

    assert category_response.status_code == 201

    category_id = category_response.json()["id"]

    delete_response = client.delete(
        f"/categories/{category_id}",
        headers=admin_headers,
    )

    assert delete_response.status_code == 204

    response = create_product(
        client,
        admin_headers,
        category_id=category_id,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Category is inactive"


def test_update_product_with_inactive_category(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    first_category_response = create_category(
        client,
        admin_headers,
        name="Electronics",
    )

    second_category_response = create_category(
        client,
        admin_headers,
        name="Computers",
    )

    assert first_category_response.status_code == 201
    assert second_category_response.status_code == 201

    first_category_id = first_category_response.json()["id"]
    second_category_id = second_category_response.json()["id"]

    create_response = create_product(
        client,
        admin_headers,
        category_id=first_category_id,
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/categories/{second_category_id}",
        headers=admin_headers,
    )

    assert delete_response.status_code == 204

    response = client.patch(
        f"/products/{product_id}",
        headers=admin_headers,
        json={
            "category_id": second_category_id,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Category is inactive"


def test_update_stock_cannot_go_below_reserved_stock(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_response = create_product(
        client,
        admin_headers,
        stock=20,
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    product = db.scalar(
        select(Product).where(Product.id == product_id)
    )

    assert product is not None

    product.reserved_stock = 10
    db.commit()

    response = client.patch(
        f"/products/{product_id}",
        headers=admin_headers,
        json={
            "stock": 9,
        },
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Stock cannot be lower than reserved stock"
    )


def test_update_stock_equal_to_reserved_stock(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_response = create_product(
        client,
        admin_headers,
        stock=20,
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    product = db.scalar(
        select(Product).where(Product.id == product_id)
    )

    assert product is not None

    product.reserved_stock = 10
    db.commit()

    response = client.patch(
        f"/products/{product_id}",
        headers=admin_headers,
        json={
            "stock": 10,
        },
    )

    assert response.status_code == 200
    assert response.json()["stock"] == 10


def test_update_product_is_active(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_response = create_product(
        client,
        admin_headers,
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    response = client.patch(
        f"/products/{product_id}",
        headers=admin_headers,
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_delete_product(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_response = create_product(
        client,
        admin_headers,
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    response = client.delete(
        f"/products/{product_id}",
        headers=admin_headers,
    )

    assert response.status_code == 204


def test_delete_product_is_soft_delete(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_response = create_product(
        client,
        admin_headers,
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/products/{product_id}",
        headers=admin_headers,
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/products/{product_id}",
    )

    assert get_response.status_code == 200

    data = get_response.json()

    assert data["id"] == product_id
    assert data["is_active"] is False


def test_delete_product_as_customer(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_response = create_product(
        client,
        admin_headers,
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    customer_headers = create_authenticated_user(
        client,
        email="customer@example.com",
    )

    response = client.delete(
        f"/products/{product_id}",
        headers=customer_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_delete_nonexistent_product(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    response = client.delete(
        "/products/999999",
        headers=admin_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_create_product_invalid_data(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    response = client.post(
        "/products",
        headers=admin_headers,
        json={
            "name": "",
            "price": "-10.00",
            "stock": -5,
        },
    )

    assert response.status_code == 422


def test_create_product_without_required_fields(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    response = client.post(
        "/products",
        headers=admin_headers,
        json={},
    )

    assert response.status_code == 422


def test_update_product_invalid_data(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_response = create_product(
        client,
        admin_headers,
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    response = client.patch(
        f"/products/{product_id}",
        headers=admin_headers,
        json={
            "price": -100,
        },
    )

    assert response.status_code == 422


def test_update_product_empty_body(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_response = create_product(
        client,
        admin_headers,
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    response = client.patch(
        f"/products/{product_id}",
        headers=admin_headers,
        json={},
    )

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def test_filter_products_by_search(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    for name in [
        "Gaming Laptop",
        "Office Laptop",
        "Smartphone",
    ]:
        response = create_product(
            client,
            admin_headers,
            name=name,
        )

        assert response.status_code == 201

    response = client.get(
        "/products?search=laptop"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2

    assert data["items"][0]["name"] == "Gaming Laptop"
    assert data["items"][1]["name"] == "Office Laptop"


def test_filter_products_by_category(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    electronics_response = create_category(
        client,
        admin_headers,
        name="Electronics",
    )

    computers_response = create_category(
        client,
        admin_headers,
        name="Computers",
    )

    assert electronics_response.status_code == 201
    assert computers_response.status_code == 201

    electronics_id = electronics_response.json()["id"]
    computers_id = computers_response.json()["id"]

    create_product(
        client,
        admin_headers,
        name="Phone",
        category_id=electronics_id,
    )

    create_product(
        client,
        admin_headers,
        name="Laptop",
        category_id=computers_id,
    )

    create_product(
        client,
        admin_headers,
        name="Headphones",
        category_id=electronics_id,
    )

    response = client.get(
        f"/products?category_id={electronics_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2

    assert data["items"][0]["name"] == "Phone"
    assert data["items"][1]["name"] == "Headphones"


def test_filter_products_by_is_active(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    first_response = create_product(
        client,
        admin_headers,
        name="Active Product",
    )

    second_response = create_product(
        client,
        admin_headers,
        name="Inactive Product",
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    inactive_product_id = second_response.json()["id"]

    update_response = client.patch(
        f"/products/{inactive_product_id}",
        headers=admin_headers,
        json={
            "is_active": False,
        },
    )

    assert update_response.status_code == 200

    response = client.get(
        "/products?is_active=true"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Active Product"


def test_filter_products_by_inactive_status(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    active_response = create_product(
        client,
        admin_headers,
        name="Active Product",
    )

    inactive_response = create_product(
        client,
        admin_headers,
        name="Inactive Product",
    )

    assert active_response.status_code == 201
    assert inactive_response.status_code == 201

    inactive_product_id = inactive_response.json()["id"]

    update_response = client.patch(
        f"/products/{inactive_product_id}",
        headers=admin_headers,
        json={
            "is_active": False,
        },
    )

    assert update_response.status_code == 200

    response = client.get(
        "/products?is_active=false"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Inactive Product"


def test_filter_products_no_results(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_product(
        client,
        admin_headers,
        name="Laptop",
    )

    response = client.get(
        "/products?search=phone"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["total"] == 0


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------


def test_sort_products_by_price_ascending(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_product(
        client,
        admin_headers,
        name="Expensive",
        price="3000.00",
    )

    create_product(
        client,
        admin_headers,
        name="Cheap",
        price="500.00",
    )

    create_product(
        client,
        admin_headers,
        name="Medium",
        price="1500.00",
    )

    response = client.get(
        "/products?sort_by=price&sort_order=asc"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"][0]["name"] == "Cheap"
    assert data["items"][1]["name"] == "Medium"
    assert data["items"][2]["name"] == "Expensive"


def test_sort_products_by_price_descending(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_product(
        client,
        admin_headers,
        name="Expensive",
        price="3000.00",
    )

    create_product(
        client,
        admin_headers,
        name="Cheap",
        price="500.00",
    )

    create_product(
        client,
        admin_headers,
        name="Medium",
        price="1500.00",
    )

    response = client.get(
        "/products?sort_by=price&sort_order=desc"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"][0]["name"] == "Expensive"
    assert data["items"][1]["name"] == "Medium"
    assert data["items"][2]["name"] == "Cheap"


def test_sort_products_by_name_ascending(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_product(
        client,
        admin_headers,
        name="Tablet",
    )

    create_product(
        client,
        admin_headers,
        name="Laptop",
    )

    create_product(
        client,
        admin_headers,
        name="Phone",
    )

    response = client.get(
        "/products?sort_by=name&sort_order=asc"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"][0]["name"] == "Laptop"
    assert data["items"][1]["name"] == "Phone"
    assert data["items"][2]["name"] == "Tablet"


def test_sort_products_by_name_descending(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    create_product(
        client,
        admin_headers,
        name="Tablet",
    )

    create_product(
        client,
        admin_headers,
        name="Laptop",
    )

    create_product(
        client,
        admin_headers,
        name="Phone",
    )

    response = client.get(
        "/products?sort_by=name&sort_order=desc"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"][0]["name"] == "Tablet"
    assert data["items"][1]["name"] == "Phone"
    assert data["items"][2]["name"] == "Laptop"


def test_sort_products_by_id_descending(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    first_response = create_product(
        client,
        admin_headers,
        name="First",
    )

    second_response = create_product(
        client,
        admin_headers,
        name="Second",
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_id = first_response.json()["id"]
    second_id = second_response.json()["id"]

    response = client.get(
        "/products?sort_by=id&sort_order=desc"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"][0]["id"] == second_id
    assert data["items"][1]["id"] == first_id


def test_sort_products_invalid_sort_by(client):
    response = client.get(
        "/products?sort_by=invalid"
    )

    assert response.status_code == 422


def test_sort_products_invalid_sort_order(client):
    response = client.get(
        "/products?sort_order=invalid"
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Combined filtering, sorting and pagination
# ---------------------------------------------------------------------------


def test_filter_sort_and_paginate_products(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    category_response = create_category(
        client,
        admin_headers,
        name="Laptops",
    )

    assert category_response.status_code == 201

    category_id = category_response.json()["id"]

    create_product(
        client,
        admin_headers,
        name="Laptop A",
        price="3000.00",
        category_id=category_id,
    )

    create_product(
        client,
        admin_headers,
        name="Laptop B",
        price="1000.00",
        category_id=category_id,
    )

    create_product(
        client,
        admin_headers,
        name="Laptop C",
        price="2000.00",
        category_id=category_id,
    )

    create_product(
        client,
        admin_headers,
        name="Phone",
        price="500.00",
    )

    response = client.get(
        f"/products"
        f"?category_id={category_id}"
        f"&sort_by=price"
        f"&sort_order=asc"
        f"&page=1"
        f"&limit=2"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["total"] == 3

    assert len(data["items"]) == 2
    assert data["items"][0]["name"] == "Laptop B"
    assert data["items"][1]["name"] == "Laptop C"


def test_filter_and_paginate_products(client, db):
    admin_headers = create_admin(
        client,
        db,
    )

    for name in [
        "Gaming Laptop",
        "Office Laptop",
        "Student Laptop",
    ]:
        response = create_product(
            client,
            admin_headers,
            name=name,
        )

        assert response.status_code == 201

    create_product(
        client,
        admin_headers,
        name="Phone",
    )

    response = client.get(
        "/products?search=laptop&page=2&limit=2"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 2
    assert data["limit"] == 2
    assert data["total"] == 3

    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Student Laptop"
