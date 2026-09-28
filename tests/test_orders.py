import pytest
from sqlalchemy import select
from decimal import Decimal

from app.auth.security import create_access_token
from app.orders.models import Order, OrderAddress
from app.products.models import Product
from app.orders.state_machine import OrderStatus
from app.users.models import User


def register_user(client, email="order@example.com"):
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123",
            "first_name": "Order",
            "last_name": "User",
        },
    )

    assert response.status_code == 201

    return response.json()


def login_user(client, email="order@example.com"):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "StrongPassword123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def make_user_admin(db, email="order@example.com"):
    user = db.scalar(
        select(User).where(
            User.email == email,
        )
    )

    assert user is not None

    user.role = "admin"
    db.commit()


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_address(
    client,
    token,
    title="Home",
    recipient_name="Order User",
    phone="09120000000",
    province="Tehran",
    city="Tehran",
    address_line="Test Street, Test Alley",
    postal_code="1234567890",
):
    response = client.post(
        "/addresses",
        json={
            "title": title,
            "recipient_name": recipient_name,
            "phone": phone,
            "province": province,
            "city": city,
            "address_line": address_line,
            "postal_code": postal_code,
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    return response.json()


def create_product(
    client,
    admin_token,
    name="Laptop",
    price="1000.00",
    stock=10,
):
    response = client.post(
        "/products",
        json={
            "name": name,
            "description": "Test product",
            "price": price,
            "stock": stock,
        },
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 201

    return response.json()


def add_to_cart(
    client,
    token,
    product_id,
    quantity,
):
    response = client.post(
        "/cart/items",
        json={
            "product_id": product_id,
            "quantity": quantity,
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    return response.json()


def checkout(
    client,
    token,
    address_id,
):
    response = client.post(
        "/orders/checkout",
        json={
            "address_id": address_id,
        },
        headers=auth_headers(token),
    )

    return response


def create_order(
    client,
    token,
    product_id,
    quantity=1,
):
    add_to_cart(
        client,
        token,
        product_id,
        quantity,
    )

    address = create_address(
        client,
        token,
    )

    response = checkout(
        client,
        token,
        address["id"],
    )

    assert response.status_code == 201

    return response.json()


def test_checkout_requires_authentication(client):
    response = client.post(
        "/orders/checkout",
    )

    assert response.status_code in {401, 403}


def test_checkout_requires_address_id(client):
    register_user(client)
    token = login_user(client)

    response = client.post(
        "/orders/checkout",
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_checkout_empty_cart_returns_404(client):
    register_user(client)
    token = login_user(client)

    address = create_address(
        client,
        token,
    )

    response = checkout(
        client,
        token,
        address["id"],
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Cart is empty"


def test_successful_checkout_creates_order(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        price="100.00",
        stock=10,
    )

    add_to_cart(
        client,
        token,
        product["id"],
        2,
    )

    address = create_address(
        client,
        token,
    )

    response = checkout(
        client,
        token,
        address["id"],
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "pending_payment"
    assert data["subtotal"] == "200.00"
    assert data["discount_amount"] == "0.00"
    assert data["shipping_amount"] == "0.00"
    assert data["tax_amount"] == "0.00"
    assert data["total_amount"] == "200.00"

    assert data["address"]["recipient_name"] == "Order User"
    assert data["address"]["phone"] == "09120000000"
    assert data["address"]["province"] == "Tehran"
    assert data["address"]["city"] == "Tehran"
    assert data["address"]["address_line"] == "Test Street, Test Alley"
    assert data["address"]["postal_code"] == "1234567890"

    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["product_id"] == product["id"]
    assert item["product_name"] == product["name"]
    assert item["unit_price"] == "100.00"
    assert item["quantity"] == 2
    assert item["total_price"] == "200.00"


def test_checkout_reserves_product_stock(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        stock=10,
    )

    add_to_cart(
        client,
        token,
        product["id"],
        3,
    )

    address = create_address(
        client,
        token,
    )

    response = checkout(
        client,
        token,
        address["id"],
    )

    assert response.status_code == 201

    product_response = client.get(
        f"/products/{product['id']}",
    )

    assert product_response.status_code == 200
    assert product_response.json()["stock"] == 10
    assert product_response.json()["reserved_stock"] == 3
    assert product_response.json()["available_stock"] == 7

def test_checkout_clears_cart(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        stock=10,
    )

    add_to_cart(
        client,
        token,
        product["id"],
        2,
    )

    address = create_address(
        client,
        token,
    )

    checkout_response = checkout(
        client,
        token,
        address["id"],
    )

    assert checkout_response.status_code == 201

    cart_response = client.get(
        "/cart",
        headers=auth_headers(token),
    )

    assert cart_response.status_code == 200
    assert cart_response.json()["items"] == []


def test_checkout_multiple_products(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product_one = create_product(
        client,
        admin_token,
        name="Keyboard",
        price="50.00",
        stock=10,
    )

    product_two = create_product(
        client,
        admin_token,
        name="Mouse",
        price="25.00",
        stock=10,
    )

    add_to_cart(
        client,
        token,
        product_one["id"],
        2,
    )

    add_to_cart(
        client,
        token,
        product_two["id"],
        3,
    )

    address = create_address(
        client,
        token,
    )

    response = checkout(
        client,
        token,
        address["id"],
    )

    assert response.status_code == 201

    data = response.json()

    assert data["subtotal"] == "175.00"
    assert data["total_amount"] == "175.00"
    assert len(data["items"]) == 2


def test_checkout_insufficient_stock_fails(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        stock=3,
    )

    add_to_cart(
        client,
        token,
        product["id"],
        3,
    )

    db_product = db.scalar(
        select(Product).where(
            Product.id == product["id"],
        )
    )

    assert db_product is not None

    db_product.stock = 2
    db.commit()

    address = create_address(
        client,
        token,
    )

    response = checkout(
        client,
        token,
        address["id"],
    )

    assert response.status_code == 409
    assert "Insufficient stock" in response.json()["detail"]


def test_failed_checkout_does_not_reduce_stock(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        stock=3,
    )

    add_to_cart(
        client,
        token,
        product["id"],
        3,
    )

    db_product = db.scalar(
        select(Product).where(
            Product.id == product["id"],
        )
    )

    assert db_product is not None

    db_product.stock = 2
    db.commit()

    address = create_address(
        client,
        token,
    )

    response = checkout(
        client,
        token,
        address["id"],
    )

    assert response.status_code == 409

    product_response = client.get(
        f"/products/{product['id']}",
    )

    assert product_response.status_code == 200
    assert product_response.json()["stock"] == 2


def test_checkout_inactive_product_fails(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        stock=10,
    )

    add_to_cart(
        client,
        token,
        product["id"],
        1,
    )

    deactivate_response = client.patch(
        f"/products/{product['id']}",
        json={
            "is_active": False,
        },
        headers=auth_headers(admin_token),
    )

    assert deactivate_response.status_code == 200

    address = create_address(
        client,
        token,
    )

    checkout_response = checkout(
        client,
        token,
        address["id"],
    )

    assert checkout_response.status_code == 409
    assert "Product is inactive" in checkout_response.json()["detail"]


def test_checkout_snapshots_product_name_and_price(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        name="Original Product",
        price="100.00",
        stock=10,
    )

    add_to_cart(
        client,
        token,
        product["id"],
        2,
    )

    update_response = client.patch(
        f"/products/{product['id']}",
        json={
            "name": "Updated Product",
            "price": "150.00",
        },
        headers=auth_headers(admin_token),
    )

    assert update_response.status_code == 200

    address = create_address(
        client,
        token,
    )

    checkout_response = checkout(
        client,
        token,
        address["id"],
    )

    assert checkout_response.status_code == 201

    item = checkout_response.json()["items"][0]

    assert item["product_name"] == "Updated Product"
    assert item["unit_price"] == "150.00"
    assert item["total_price"] == "300.00"


def test_checkout_rejects_another_users_address(client):
    register_user(
        client,
        email="first@example.com",
    )

    first_token = login_user(
        client,
        email="first@example.com",
    )

    first_address = create_address(
        client,
        first_token,
        recipient_name="First User",
    )

    register_user(
        client,
        email="second@example.com",
    )

    second_token = login_user(
        client,
        email="second@example.com",
    )

    response = checkout(
        client,
        second_token,
        first_address["id"],
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Address not found"


def test_checkout_snapshots_address(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        price="100.00",
        stock=10,
    )

    add_to_cart(
        client,
        token,
        product["id"],
        1,
    )

    address = create_address(
        client,
        token,
        recipient_name="Original Recipient",
        phone="09121111111",
        province="Tehran",
        city="Tehran",
        address_line="Original Address",
        postal_code="1111111111",
    )

    response = checkout(
        client,
        token,
        address["id"],
    )

    assert response.status_code == 201

    order = response.json()

    assert order["address"]["recipient_name"] == "Original Recipient"
    assert order["address"]["phone"] == "09121111111"
    assert order["address"]["address_line"] == "Original Address"
    assert order["address"]["postal_code"] == "1111111111"


def test_order_address_does_not_change_when_original_address_is_updated(
    client,
    db,
):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        price="100.00",
        stock=10,
    )

    add_to_cart(
        client,
        token,
        product["id"],
        1,
    )

    address = create_address(
        client,
        token,
        recipient_name="Original Recipient",
        address_line="Original Address",
    )

    checkout_response = checkout(
        client,
        token,
        address["id"],
    )

    assert checkout_response.status_code == 201

    order_id = checkout_response.json()["id"]

    update_response = client.patch(
        f"/addresses/{address['id']}",
        json={
            "recipient_name": "Updated Recipient",
            "address_line": "Updated Address",
        },
        headers=auth_headers(token),
    )

    assert update_response.status_code == 200

    order_response = client.get(
        f"/orders/{order_id}",
        headers=auth_headers(token),
    )

    assert order_response.status_code == 200

    order = order_response.json()

    assert order["address"]["recipient_name"] == "Original Recipient"
    assert order["address"]["address_line"] == "Original Address"


def test_user_can_list_own_orders(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        price="50.00",
        stock=10,
    )

    checkout_response = create_order(
        client,
        token,
        product["id"],
        2,
    )

    response = client.get(
        "/orders",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 20
    assert data["total"] == 1
    assert len(data["items"]) == 1

    assert data["items"][0]["id"] == checkout_response["id"]
    assert len(data["items"][0]["items"]) == 1
    assert data["items"][0]["address"]["id"] if "id" in data["items"][0]["address"] else True


def test_user_can_get_own_order(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        price="75.00",
        stock=10,
    )

    add_to_cart(
        client,
        token,
        product["id"],
        1,
    )

    address = create_address(
        client,
        token,
    )

    checkout_response = checkout(
        client,
        token,
        address["id"],
    )

    assert checkout_response.status_code == 201

    order_id = checkout_response.json()["id"]

    response = client.get(
        f"/orders/{order_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == order_id
    assert response.json()["total_amount"] == "75.00"
    assert response.json()["address"]["recipient_name"] == "Order User"


def test_user_cannot_access_another_users_order(client, db):
    register_user(
        client,
        email="first@example.com",
    )

    first_token = login_user(
        client,
        email="first@example.com",
    )

    make_user_admin(
        db,
        email="first@example.com",
    )

    first_admin_token = login_user(
        client,
        email="first@example.com",
    )

    product = create_product(
        client,
        first_admin_token,
        price="100.00",
        stock=10,
    )

    add_to_cart(
        client,
        first_token,
        product["id"],
        1,
    )

    first_address = create_address(
        client,
        first_token,
    )

    checkout_response = checkout(
        client,
        first_token,
        first_address["id"],
    )

    assert checkout_response.status_code == 201

    order_id = checkout_response.json()["id"]

    register_user(
        client,
        email="second@example.com",
    )

    second_token = login_user(
        client,
        email="second@example.com",
    )

    response = client.get(
        f"/orders/{order_id}",
        headers=auth_headers(second_token),
    )

    assert response.status_code == 404


def test_user_only_sees_own_orders(client, db):
    register_user(
        client,
        email="first@example.com",
    )

    first_token = login_user(
        client,
        email="first@example.com",
    )

    make_user_admin(
        db,
        email="first@example.com",
    )

    first_admin_token = login_user(
        client,
        email="first@example.com",
    )

    product = create_product(
        client,
        first_admin_token,
        price="100.00",
        stock=10,
    )

    add_to_cart(
        client,
        first_token,
        product["id"],
        1,
    )

    first_address = create_address(
        client,
        first_token,
    )

    first_order = checkout(
        client,
        first_token,
        first_address["id"],
    )

    assert first_order.status_code == 201

    register_user(
        client,
        email="second@example.com",
    )

    second_token = login_user(
        client,
        email="second@example.com",
    )

    response = client.get(
        "/orders",
        headers=auth_headers(second_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["limit"] == 20


def test_get_nonexistent_order_returns_404(client):
    register_user(client)
    token = login_user(client)

    response = client.get(
        "/orders/999999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_get_orders_empty(client):
    register_user(client)
    token = login_user(client)

    response = client.get(
        "/orders",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["page"] == 1
    assert data["limit"] == 20
    assert data["total"] == 0


def test_get_orders_page_one(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        price="10.00",
        stock=100,
    )

    for _ in range(5):
        create_order(
            client,
            token,
            product["id"],
        )

    response = client.get(
        "/orders?page=1&limit=2",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["total"] == 5
    assert len(data["items"]) == 2


def test_get_orders_page_two(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        price="10.00",
        stock=100,
    )

    order_ids = []

    for _ in range(5):
        order = create_order(
            client,
            token,
            product["id"],
        )
        order_ids.append(order["id"])

    response = client.get(
        "/orders?page=2&limit=2",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 2
    assert data["limit"] == 2
    assert data["total"] == 5
    assert len(data["items"]) == 2

    assert data["items"][0]["id"] == order_ids[2]
    assert data["items"][1]["id"] == order_ids[1]


def test_get_orders_empty_page(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        stock=100,
    )

    create_order(
        client,
        token,
        product["id"],
    )

    response = client.get(
        "/orders?page=2&limit=20",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["page"] == 2
    assert data["limit"] == 20
    assert data["total"] == 1


def test_get_orders_invalid_page(client):
    register_user(client)
    token = login_user(client)

    response = client.get(
        "/orders?page=0",
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_get_orders_invalid_limit_zero(client):
    register_user(client)
    token = login_user(client)

    response = client.get(
        "/orders?limit=0",
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_get_orders_invalid_limit_too_large(client):
    register_user(client)
    token = login_user(client)

    response = client.get(
        "/orders?limit=101",
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_get_orders_custom_limit(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        stock=100,
    )

    for _ in range(5):
        create_order(
            client,
            token,
            product["id"],
        )

    response = client.get(
        "/orders?page=1&limit=3",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 3
    assert data["total"] == 5
    assert len(data["items"]) == 3



# ============================================================
# Order Cancellation Tests
# ============================================================


def test_cancel_pending_payment_order(client, db):
    user = User(
        email="cancel@example.com",
        password_hash="hashed-password",
        first_name="Cancel",
        last_name="User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    order = Order(
    user_id=user.id,
    status=OrderStatus.PENDING_PAYMENT.value,
    subtotal=Decimal("100.00"),
    discount_amount=Decimal("0.00"),
    shipping_amount=Decimal("0.00"),
    tax_amount=Decimal("0.00"),
    total_amount=Decimal("100.00"),
)

    order.address = OrderAddress(
    recipient_name="Cancel User",
    phone="09120000000",
    province="Test Province",
    city="Test City",
    address_line="Test Address",
    postal_code="1234567890",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    token = create_access_token(user.id)

    response = client.post(
        f"/orders/{order.id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == OrderStatus.CANCELLED.value

    db.refresh(order)

    assert order.status == OrderStatus.CANCELLED.value


def test_cancel_order_of_another_user_returns_404(client, db):
    owner = User(
        email="owner@example.com",
        password_hash="hashed-password",
        first_name="Owner",
        last_name="User",
    )

    other_user = User(
        email="other@example.com",
        password_hash="hashed-password",
        first_name="Other",
        last_name="User",
    )

    db.add_all([owner, other_user])
    db.commit()
    db.refresh(owner)
    db.refresh(other_user)

    order = Order(
        user_id=owner.id,
        status=OrderStatus.PENDING_PAYMENT.value,
        subtotal=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        shipping_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    token = create_access_token(other_user.id)

    response = client.post(
        f"/orders/{order.id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404

    db.refresh(order)

    assert order.status == OrderStatus.PENDING_PAYMENT.value


@pytest.mark.parametrize(
    "current_status",
    [
        OrderStatus.PAID,
        OrderStatus.SHIPPED,
        OrderStatus.DELIVERED,
        OrderStatus.CANCELLED,
    ],
)
def test_cancel_order_with_invalid_status_returns_409(
    client,
    db,
    current_status,
):
    user = User(
        email=f"{current_status.value}@example.com",
        password_hash="hashed-password",
        first_name="Test",
        last_name="User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    order = Order(
        user_id=user.id,
        status=current_status.value,
        subtotal=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        shipping_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    token = create_access_token(user.id)

    response = client.post(
        f"/orders/{order.id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409

    db.refresh(order)

    assert order.status == current_status.value


def test_cancel_nonexistent_order_returns_404(client, db):
    user = User(
        email="missing-order@example.com",
        password_hash="hashed-password",
        first_name="Missing",
        last_name="Order",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)

    response = client.post(
        "/orders/999999/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
