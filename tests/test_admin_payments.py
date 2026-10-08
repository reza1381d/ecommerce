from tests.admin_helpers import auth_headers, make_order, make_payment, make_user


def test_admin_payment_list_filters_and_returns_order_customer(client, db):
    admin = make_user(db, email="admin@example.com", role="admin")
    customer = make_user(db)
    order = make_order(db, customer)
    payment = make_payment(db, order, provider="manual")

    response = client.get(
        "/admin/payments?provider=manual&search=customer",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == payment.id
    assert body["items"][0]["order_status"] == order.status
    assert body["items"][0]["customer"]["email"] == customer.email


def test_admin_payment_list_requires_admin(client, db):
    customer = make_user(db)
    assert client.get("/admin/payments").status_code == 401
    assert client.get("/admin/payments", headers=auth_headers(customer)).status_code == 403

