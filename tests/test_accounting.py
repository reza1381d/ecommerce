from datetime import datetime, timezone
from decimal import Decimal

from tests.admin_helpers import auth_headers, make_order, make_order_item, make_payment, make_user


def test_dashboard_stats_and_product_sales_use_payment_and_order_data(client, db):
    admin = make_user(db, email="admin@example.com", role="admin")
    customer = make_user(db)
    order = make_order(db, customer, status="paid")
    make_order_item(db, order, quantity=4)
    make_payment(db, order, amount=Decimal("200"))
    headers = auth_headers(admin)

    stats = client.get("/admin/dashboard/stats?period=7d", headers=headers)
    assert stats.status_code == 200
    assert stats.json()["total_orders"] == 1
    assert stats.json()["paid_orders"] == 1
    assert stats.json()["total_revenue"] == "200"

    products = client.get("/admin/dashboard/product-sales?period=7d", headers=headers)
    assert products.status_code == 200
    assert products.json()["items"][0]["quantity_sold"] == 4
    assert products.json()["items"][0]["revenue"] == "200"


def test_sales_timeline_honors_custom_day_range_and_zero_buckets(client, db):
    admin = make_user(db, email="admin@example.com", role="admin")
    customer = make_user(db)
    order = make_order(db, customer)
    make_order_item(db, order, quantity=3)
    make_payment(
        db,
        order,
        amount=Decimal("150"),
        created_at=datetime(2025, 2, 2, 12, tzinfo=timezone.utc),
    )

    response = client.get(
        "/admin/dashboard/sales-timeline?group_by=day&start_date=2025-02-01&end_date=2025-02-03",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["period"] for item in items] == ["2025-02-01", "2025-02-02", "2025-02-03"]
    assert items[0]["revenue"] == "0"
    assert items[1]["revenue"] == "150"
    assert items[1]["orders"] == 1
    assert items[1]["units_sold"] == 3
    assert items[2]["orders"] == 0


def test_sales_timeline_custom_month_range_and_validation(client, db):
    admin = make_user(db, email="admin@example.com", role="admin")
    headers = auth_headers(admin)

    response = client.get(
        "/admin/dashboard/sales-timeline?group_by=month&start_date=2024-12-15&end_date=2025-02-02",
        headers=headers,
    )
    assert response.status_code == 200
    assert [item["period"] for item in response.json()["items"]] == ["2024-12", "2025-01", "2025-02"]

    response = client.get(
        "/admin/dashboard/sales-timeline?group_by=year&start_date=2024-04-01&end_date=2025-03-31",
        headers=headers,
    )
    assert response.status_code == 200
    assert [item["period"] for item in response.json()["items"]] == ["2024", "2025"]

    assert client.get(
        "/admin/dashboard/sales-timeline?start_date=2025-01-01",
        headers=headers,
    ).status_code == 422
    assert client.get(
        "/admin/dashboard/sales-timeline?start_date=2025-01-02&end_date=2025-01-01",
        headers=headers,
    ).status_code == 422
    assert client.get(
        "/admin/dashboard/sales-timeline?group_by=day&start_date=2024-01-01&end_date=2025-01-01",
        headers=headers,
    ).status_code == 422

