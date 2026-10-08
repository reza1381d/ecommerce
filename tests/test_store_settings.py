from tests.admin_helpers import auth_headers, make_user


def test_public_store_settings_returns_defaults(client):
    response = client.get("/store/settings")

    assert response.status_code == 200
    body = response.json()
    assert body["store_name"] == "فروشگاه اینترنتی"
    assert body["palette"] == "blue"
    assert body["currency_unit"] == "toman"
    assert body["home_hero_title"]


def test_admin_can_update_public_store_settings(client, db):
    admin = make_user(db, email="admin@example.com", role="admin")
    payload = {
        "store_name": "فروشگاه آزمایشی",
        "palette": "fuchsia",
        "currency_unit": "rial",
        "home_hero_badge": "پیشنهاد ویژه",
        "home_hero_title": "عنوان جدید",
        "home_hero_description": "توضیحات جدید",
        "home_hero_button_label": "دیدن محصولات",
    }

    response = client.put("/admin/store/settings", headers=auth_headers(admin), json=payload)
    assert response.status_code == 200
    assert response.json()["currency_unit"] == "rial"
    assert client.get("/store/settings").json() == response.json()


def test_store_settings_update_requires_admin_and_valid_values(client, db):
    customer = make_user(db)
    payload = {
        "store_name": "Store",
        "palette": "unknown",
        "currency_unit": "dollar",
        "home_hero_badge": "Badge",
        "home_hero_title": "Title",
        "home_hero_description": "Description",
        "home_hero_button_label": "Shop",
    }
    assert client.put("/admin/store/settings", json=payload).status_code == 401
    assert client.put("/admin/store/settings", headers=auth_headers(customer), json=payload).status_code == 403

    admin = make_user(db, email="admin@example.com", role="admin")
    assert client.put("/admin/store/settings", headers=auth_headers(admin), json=payload).status_code == 422

