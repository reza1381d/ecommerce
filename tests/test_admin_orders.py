from tests.admin_helpers import auth_headers, make_order, make_payment, make_user


def test_admin_orders_include_customer_and_latest_payment(client, db):
    admin = make_user(db, email="admin@example.com", role="admin")
    customer = make_user(db)
    order = make_order(db, customer)
    make_payment(db, order, status="failed")
    latest = make_payment(db, order, status="successful")

    response = client.get("/admin/orders", headers=auth_headers(admin))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    item = body["items"][0]
    assert item["customer"]["email"] == customer.email
    assert item["payment_status"] == "successful"
    assert item["latest_payment"]["id"] == latest.id


def test_admin_orders_filter_unpaid_and_payment_status(client, db):
    admin = make_user(db, email="admin@example.com", role="admin")
    customer = make_user(db)
    paid_order = make_order(db, customer)
    make_payment(db, paid_order, status="successful")
    unpaid_order = make_order(db, customer, total=200)

    response = client.get("/admin/orders?payment_status=unpaid", headers=auth_headers(admin))
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [unpaid_order.id]

    response = client.get("/admin/orders?payment_status=successful", headers=auth_headers(admin))
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [paid_order.id]

