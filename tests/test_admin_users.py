from tests.admin_helpers import auth_headers, make_user


def test_admin_user_list_supports_search_sort_and_pagination(client, db):
    admin = make_user(db, email="admin@example.com", role="admin")
    make_user(db, email="zara@example.com")
    make_user(db, email="ali@example.com")
    headers = auth_headers(admin)

    response = client.get(
        "/admin/users?page=1&limit=1&sort_by=email&sort_order=asc",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["limit"] == 1
    assert body["items"][0]["email"] == "admin@example.com"

    response = client.get("/admin/users?search=zara", headers=headers)
    assert response.status_code == 200
    assert [item["email"] for item in response.json()["items"]] == ["zara@example.com"]


def test_admin_user_list_requires_admin(client, db):
    customer = make_user(db)
    assert client.get("/admin/users").status_code == 401
    assert client.get("/admin/users", headers=auth_headers(customer)).status_code == 403

