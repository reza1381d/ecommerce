from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.inventory.service import InventoryService
from app.orders.models import Order, OrderItem
from app.payments.models import Payment
from app.reservations.models import Reservation
from app.reservations.state_machine import ReservationStatus
from app.products.models import Product
from app.users.models import User


def register_user(
    client,
    email="payment@example.com",
):
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123",
            "first_name": "Payment",
            "last_name": "User",
        },
    )

    assert response.status_code == 201

    return response.json()


def login_user(
    client,
    email="payment@example.com",
):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "StrongPassword123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def make_user_admin(
    db,
    email="payment@example.com",
):
    user = db.scalar(
        select(User).where(
            User.email == email,
        )
    )

    assert user is not None

    user.role = "admin"
    db.commit()


def create_product(
    client,
    admin_token,
    name="Laptop",
    price="100.00",
    stock=10,
):
    response = client.post(
        "/products",
        json={
            "name": name,
            "description": "Payment test product",
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


def create_address(
    client,
    token,
):
    response = client.post(
        "/addresses",
        json={
            "title": "Home",
            "recipient_name": "Payment User",
            "phone": "09120000000",
            "province": "Tehran",
            "city": "Tehran",
            "address_line": "Test address",
            "postal_code": "1234567890",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    return response.json()


def create_order(
    client,
    user_token,
    product_id,
    quantity=1,
):
    add_to_cart(
        client,
        user_token,
        product_id,
        quantity,
    )

    address = create_address(
        client,
        user_token,
    )

    response = client.post(
        "/orders/checkout",
        json={
            "address_id": address["id"],
        },
        headers=auth_headers(user_token),
    )

    assert response.status_code == 201

    return response.json()


def create_multi_item_order(
    client,
    user_token,
    items,
):
    for product_id, quantity in items:
        add_to_cart(
            client,
            user_token,
            product_id,
            quantity,
        )

    address = create_address(
        client,
        user_token,
    )

    response = client.post(
        "/orders/checkout",
        json={
            "address_id": address["id"],
        },
        headers=auth_headers(user_token),
    )

    assert response.status_code == 201

    return response.json()


def get_product(
    db,
    product_id,
):
    product = db.scalar(
        select(Product).where(
            Product.id == product_id,
        )
    )

    assert product is not None

    return product


def get_order_with_items(
    db,
    order_id,
):
    order = db.scalar(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(
                OrderItem.reservation
            )
        )
        .where(
            Order.id == order_id,
        )
    )

    assert order is not None

    return order


def test_create_payment_requires_authentication(client):
    response = client.post(
        "/payments",
        json={
            "order_id": 1,
        },
    )

    assert response.status_code in {401, 403}


def test_create_payment_for_nonexistent_order_returns_404(client):
    register_user(client)
    token = login_user(client)

    response = client.post(
        "/payments",
        json={
            "order_id": 999999,
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_successful_payment_creates_payment(client, db):
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

    order = create_order(
        client,
        token,
        product["id"],
        quantity=2,
    )

    response = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["order_id"] == order["id"]
    assert data["amount"] == "200"
    assert data["status"] == "successful"
    assert data["provider"] == "mock"
    assert data["provider_payment_id"].startswith("mock_")


def test_payment_amount_matches_order_total(client, db):
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

    order = create_order(
        client,
        token,
        product["id"],
        quantity=3,
    )

    response = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    payment = response.json()

    assert payment["amount"] == order["total_amount"]


def test_successful_payment_changes_order_status_to_paid(client, db):
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

    order = create_order(
        client,
        token,
        product["id"],
    )

    response = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    order_response = client.get(
        f"/orders/{order['id']}",
        headers=auth_headers(token),
    )

    assert order_response.status_code == 200
    assert order_response.json()["status"] == "paid"


def test_cannot_pay_already_paid_order(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        stock=10,
    )

    order = create_order(
        client,
        token,
        product["id"],
    )

    first_payment = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(token),
    )

    assert first_payment.status_code == 201

    second_payment = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(token),
    )

    assert second_payment.status_code == 409
    assert second_payment.json()["detail"] == "Order is not awaiting payment"


def test_payment_for_another_users_order_returns_404(client, db):
    register_user(
        client,
        email="first-payment@example.com",
    )

    first_token = login_user(
        client,
        email="first-payment@example.com",
    )

    make_user_admin(
        db,
        email="first-payment@example.com",
    )

    first_admin_token = login_user(
        client,
        email="first-payment@example.com",
    )

    product = create_product(
        client,
        first_admin_token,
        stock=10,
    )

    order = create_order(
        client,
        first_token,
        product["id"],
    )

    register_user(
        client,
        email="second-payment@example.com",
    )

    second_token = login_user(
        client,
        email="second-payment@example.com",
    )

    response = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(second_token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_get_payment_requires_authentication(client):
    response = client.get(
        "/payments/1",
    )

    assert response.status_code in {401, 403}


def test_get_payment_returns_own_payment(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        stock=10,
    )

    order = create_order(
        client,
        token,
        product["id"],
    )

    payment_response = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(token),
    )

    assert payment_response.status_code == 201

    payment_id = payment_response.json()["id"]

    response = client.get(
        f"/payments/{payment_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == payment_id


def test_get_nonexistent_payment_returns_404(client):
    register_user(client)
    token = login_user(client)

    response = client.get(
        "/payments/999999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"


def test_user_cannot_get_another_users_payment(client, db):
    register_user(
        client,
        email="first-get-payment@example.com",
    )

    first_token = login_user(
        client,
        email="first-get-payment@example.com",
    )

    make_user_admin(
        db,
        email="first-get-payment@example.com",
    )

    first_admin_token = login_user(
        client,
        email="first-get-payment@example.com",
    )

    product = create_product(
        client,
        first_admin_token,
        stock=10,
    )

    order = create_order(
        client,
        first_token,
        product["id"],
    )

    payment_response = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(first_token),
    )

    assert payment_response.status_code == 201

    payment_id = payment_response.json()["id"]

    register_user(
        client,
        email="second-get-payment@example.com",
    )

    second_token = login_user(
        client,
        email="second-get-payment@example.com",
    )

    response = client.get(
        f"/payments/{payment_id}",
        headers=auth_headers(second_token),
    )

    assert response.status_code == 404


def test_list_payments_requires_authentication(client):
    response = client.get(
        "/payments",
    )

    assert response.status_code in {401, 403}


def test_user_can_list_own_payments(client, db):
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

    order = create_order(
        client,
        token,
        product["id"],
    )

    payment_response = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(token),
    )

    assert payment_response.status_code == 201

    response = client.get(
        "/payments",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    payments = response.json()

    assert len(payments) == 1
    assert payments[0]["id"] == payment_response.json()["id"]
    assert payments[0]["order_id"] == order["id"]


def test_user_only_sees_own_payments(client, db):
    register_user(
        client,
        email="first-list-payment@example.com",
    )

    first_token = login_user(
        client,
        email="first-list-payment@example.com",
    )

    make_user_admin(
        db,
        email="first-list-payment@example.com",
    )

    first_admin_token = login_user(
        client,
        email="first-list-payment@example.com",
    )

    product = create_product(
        client,
        first_admin_token,
        stock=10,
    )

    order = create_order(
        client,
        first_token,
        product["id"],
    )

    payment_response = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(first_token),
    )

    assert payment_response.status_code == 201

    register_user(
        client,
        email="second-list-payment@example.com",
    )

    second_token = login_user(
        client,
        email="second-list-payment@example.com",
    )

    response = client.get(
        "/payments",
        headers=auth_headers(second_token),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_payment_provider_is_mock(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        stock=10,
    )

    order = create_order(
        client,
        token,
        product["id"],
    )

    response = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    assert response.json()["provider"] == "mock"


def test_payment_is_persisted_in_database(client, db):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product = create_product(
        client,
        admin_token,
        price="120.00",
        stock=10,
    )

    order = create_order(
        client,
        token,
        product["id"],
    )

    response = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    payment_id = response.json()["id"]

    payment = db.scalar(
        select(Payment).where(
            Payment.id == payment_id,
        )
    )

    assert payment is not None
    assert payment.order_id == order["id"]
    assert payment.status == "successful"
    assert payment.provider == "mock"


# ---------------------------------------------------------------------------
# Payment ↔ Reservation ↔ Inventory integration tests
# ---------------------------------------------------------------------------


def test_successful_payment_consumes_reservation_and_inventory(
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

    order = create_order(
        client,
        token,
        product["id"],
        quantity=2,
    )

    product_before = get_product(
        db,
        product["id"],
    )

    assert product_before.stock == 10
    assert product_before.reserved_stock == 2

    order_before = get_order_with_items(
        db,
        order["id"],
    )

    assert len(order_before.items) == 1

    reservation_before = order_before.items[0].reservation

    assert reservation_before is not None
    assert reservation_before.quantity == 2
    assert reservation_before.status == ReservationStatus.ACTIVE.value

    response = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    db.expire_all()

    product_after = get_product(
        db,
        product["id"],
    )

    assert product_after.stock == 8
    assert product_after.reserved_stock == 0

    order_after = get_order_with_items(
        db,
        order["id"],
    )

    reservation_after = order_after.items[0].reservation

    assert reservation_after.status == ReservationStatus.CONSUMED.value
    assert reservation_after.quantity == 2

    assert order_after.status == "paid"


def test_successful_multi_item_payment_consumes_all_inventory(
    client,
    db,
):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product_a = create_product(
        client,
        admin_token,
        name="Laptop",
        price="100.00",
        stock=10,
    )

    product_b = create_product(
        client,
        admin_token,
        name="Mouse",
        price="50.00",
        stock=20,
    )

    order = create_multi_item_order(
        client,
        token,
        [
            (product_a["id"], 2),
            (product_b["id"], 3),
        ],
    )

    product_a_before = get_product(
        db,
        product_a["id"],
    )

    product_b_before = get_product(
        db,
        product_b["id"],
    )

    assert product_a_before.stock == 10
    assert product_a_before.reserved_stock == 2

    assert product_b_before.stock == 20
    assert product_b_before.reserved_stock == 3

    response = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    db.expire_all()

    product_a_after = get_product(
        db,
        product_a["id"],
    )

    product_b_after = get_product(
        db,
        product_b["id"],
    )

    assert product_a_after.stock == 8
    assert product_a_after.reserved_stock == 0

    assert product_b_after.stock == 17
    assert product_b_after.reserved_stock == 0

    order_after = get_order_with_items(
        db,
        order["id"],
    )

    assert order_after.status == "paid"

    assert len(order_after.items) == 2

    for order_item in order_after.items:
        assert order_item.reservation is not None
        assert (
            order_item.reservation.status
            == ReservationStatus.CONSUMED.value
        )


def test_payment_failure_rolls_back_all_inventory_changes(
    client,
    db,
):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product_a = create_product(
        client,
        admin_token,
        name="Laptop",
        price="100.00",
        stock=10,
    )

    product_b = create_product(
        client,
        admin_token,
        name="Mouse",
        price="50.00",
        stock=20,
    )

    order = create_multi_item_order(
        client,
        token,
        [
            (product_a["id"], 2),
            (product_b["id"], 3),
        ],
    )

    order_before = get_order_with_items(
        db,
        order["id"],
    )

    assert len(order_before.items) == 2

    # Intentionally break the reservation/inventory invariant
    # for the second product so that payment fails after
    # the first product has already been consumed.
    product_b_db = get_product(
        db,
        product_b["id"],
    )

    assert product_b_db.reserved_stock == 3

    product_b_db.reserved_stock = 0
    db.commit()

    response = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 409

    db.expire_all()

    product_a_after = get_product(
        db,
        product_a["id"],
    )

    product_b_after = get_product(
        db,
        product_b["id"],
    )

    # Product A was consumed first inside the transaction,
    # but the failure on Product B must roll everything back.
    assert product_a_after.stock == 10
    assert product_a_after.reserved_stock == 2

    # Product B was intentionally corrupted before payment,
    # and the failed transaction must not change it further.
    assert product_b_after.stock == 20
    assert product_b_after.reserved_stock == 0

    order_after = get_order_with_items(
        db,
        order["id"],
    )

    assert order_after.status == "pending_payment"

    for order_item in order_after.items:
        assert order_item.reservation is not None
        assert (
            order_item.reservation.status
            == ReservationStatus.ACTIVE.value
        )

    payments = db.scalars(
        select(Payment).where(
            Payment.order_id == order["id"],
        )
    ).all()

    assert payments == []


def test_double_payment_does_not_change_inventory_or_reservation(
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

    order = create_order(
        client,
        token,
        product["id"],
        quantity=2,
    )

    first_payment = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(token),
    )

    assert first_payment.status_code == 201

    db.expire_all()

    product_after_first = get_product(
        db,
        product["id"],
    )

    assert product_after_first.stock == 8
    assert product_after_first.reserved_stock == 0

    order_after_first = get_order_with_items(
        db,
        order["id"],
    )

    reservation_after_first = (
        order_after_first.items[0].reservation
    )

    assert (
        reservation_after_first.status
        == ReservationStatus.CONSUMED.value
    )

    payments_after_first = db.scalars(
        select(Payment).where(
            Payment.order_id == order["id"],
        )
    ).all()

    assert len(payments_after_first) == 1

    second_payment = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(token),
    )

    assert second_payment.status_code == 409
    assert (
        second_payment.json()["detail"]
        == "Order is not awaiting payment"
    )

    db.expire_all()

    product_after_second = get_product(
        db,
        product["id"],
    )

    assert product_after_second.stock == 8
    assert product_after_second.reserved_stock == 0

    order_after_second = get_order_with_items(
        db,
        order["id"],
    )

    reservation_after_second = (
        order_after_second.items[0].reservation
    )

    assert (
        reservation_after_second.status
        == ReservationStatus.CONSUMED.value
    )

    payments_after_second = db.scalars(
        select(Payment).where(
            Payment.order_id == order["id"],
        )
    ).all()

    assert len(payments_after_second) == 1


def test_successful_payment_does_not_leave_reserved_stock(
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
        stock=15,
    )

    order = create_order(
        client,
        token,
        product["id"],
        quantity=5,
    )

    response = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    db.expire_all()

    product_after = get_product(
        db,
        product["id"],
    )

    assert product_after.stock == 10
    assert product_after.reserved_stock == 0
    assert (
        product_after.stock - product_after.reserved_stock
        == 10
    )


def test_failed_payment_does_not_create_payment_record(
    client,
    db,
):
    register_user(client)
    token = login_user(client)

    make_user_admin(db)
    admin_token = login_user(client)

    product_a = create_product(
        client,
        admin_token,
        name="Laptop",
        stock=10,
    )

    product_b = create_product(
        client,
        admin_token,
        name="Mouse",
        stock=10,
    )

    order = create_multi_item_order(
        client,
        token,
        [
            (product_a["id"], 2),
            (product_b["id"], 2),
        ],
    )

    product_b_db = get_product(
        db,
        product_b["id"],
    )

    product_b_db.reserved_stock = 0
    db.commit()

    response = client.post(
        "/payments",
        json={
            "order_id": order["id"],
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 409

    payments = db.scalars(
        select(Payment).where(
            Payment.order_id == order["id"],
        )
    ).all()

    assert payments == []
