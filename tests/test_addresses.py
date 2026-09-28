import pytest
from fastapi.testclient import TestClient


def register_user(
    client: TestClient,
    email: str,
) -> dict:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
            "phone": None,
        },
    )

    assert response.status_code == 201

    return response.json()


def login_user(
    client: TestClient,
    email: str,
) -> str:
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def address_payload(
    title: str = "Home",
) -> dict:
    return {
        "title": title,
        "recipient_name": "Test User",
        "phone": "09120000000",
        "province": "Tehran",
        "city": "Tehran",
        "address_line": "Test Street, No. 10",
        "postal_code": "1234567890",
    }


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    register_user(
        client,
        "address@example.com",
    )

    token = login_user(
        client,
        "address@example.com",
    )

    return {
        "Authorization": f"Bearer {token}",
    }


def test_create_address(
    client: TestClient,
    auth_headers: dict,
):
    response = client.post(
        "/addresses",
        headers=auth_headers,
        json=address_payload(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Home"
    assert data["city"] == "Tehran"
    assert data["is_default"] is True


def test_first_address_is_default(
    client: TestClient,
    auth_headers: dict,
):
    response = client.post(
        "/addresses",
        headers=auth_headers,
        json=address_payload(),
    )

    assert response.status_code == 201
    assert response.json()["is_default"] is True


def test_second_address_is_not_default(
    client: TestClient,
    auth_headers: dict,
):
    first_response = client.post(
        "/addresses",
        headers=auth_headers,
        json=address_payload("Home"),
    )

    second_response = client.post(
        "/addresses",
        headers=auth_headers,
        json=address_payload("Work"),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    assert first_response.json()["is_default"] is True
    assert second_response.json()["is_default"] is False


def test_list_addresses(
    client: TestClient,
    auth_headers: dict,
):
    client.post(
        "/addresses",
        headers=auth_headers,
        json=address_payload("Home"),
    )

    client.post(
        "/addresses",
        headers=auth_headers,
        json=address_payload("Work"),
    )

    response = client.get(
        "/addresses",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["title"] == "Home"
    assert data[1]["title"] == "Work"


def test_get_address(
    client: TestClient,
    auth_headers: dict,
):
    create_response = client.post(
        "/addresses",
        headers=auth_headers,
        json=address_payload(),
    )

    address_id = create_response.json()["id"]

    response = client.get(
        f"/addresses/{address_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == address_id


def test_update_address(
    client: TestClient,
    auth_headers: dict,
):
    create_response = client.post(
        "/addresses",
        headers=auth_headers,
        json=address_payload(),
    )

    address_id = create_response.json()["id"]

    response = client.patch(
        f"/addresses/{address_id}",
        headers=auth_headers,
        json={
            "city": "Mashhad",
            "address_line": "New Street, No. 20",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["city"] == "Mashhad"
    assert data["address_line"] == "New Street, No. 20"
    assert data["title"] == "Home"


def test_set_default_address(
    client: TestClient,
    auth_headers: dict,
):
    first_response = client.post(
        "/addresses",
        headers=auth_headers,
        json=address_payload("Home"),
    )

    second_response = client.post(
        "/addresses",
        headers=auth_headers,
        json=address_payload("Work"),
    )

    first_id = first_response.json()["id"]
    second_id = second_response.json()["id"]

    response = client.patch(
        f"/addresses/{second_id}/default",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["is_default"] is True

    first_check = client.get(
        f"/addresses/{first_id}",
        headers=auth_headers,
    )

    assert first_check.json()["is_default"] is False


def test_only_one_default_address_exists(
    client: TestClient,
    auth_headers: dict,
):
    addresses = []

    for title in ["Home", "Work", "Office"]:
        response = client.post(
            "/addresses",
            headers=auth_headers,
            json=address_payload(title),
        )

        addresses.append(response.json())

    third_id = addresses[2]["id"]

    response = client.patch(
        f"/addresses/{third_id}/default",
        headers=auth_headers,
    )

    assert response.status_code == 200

    response = client.get(
        "/addresses",
        headers=auth_headers,
    )

    assert response.status_code == 200

    default_addresses = [
        address
        for address in response.json()
        if address["is_default"]
    ]

    assert len(default_addresses) == 1
    assert default_addresses[0]["id"] == third_id


def test_get_other_users_address_returns_404(
    client: TestClient,
):
    register_user(
        client,
        "user1@example.com",
    )

    token1 = login_user(
        client,
        "user1@example.com",
    )

    headers1 = {
        "Authorization": f"Bearer {token1}",
    }

    create_response = client.post(
        "/addresses",
        headers=headers1,
        json=address_payload(),
    )

    address_id = create_response.json()["id"]

    register_user(
        client,
        "user2@example.com",
    )

    token2 = login_user(
        client,
        "user2@example.com",
    )

    headers2 = {
        "Authorization": f"Bearer {token2}",
    }

    response = client.get(
        f"/addresses/{address_id}",
        headers=headers2,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Address not found"


def test_update_other_users_address_returns_404(
    client: TestClient,
):
    register_user(
        client,
        "user1@example.com",
    )

    token1 = login_user(
        client,
        "user1@example.com",
    )

    headers1 = {
        "Authorization": f"Bearer {token1}",
    }

    create_response = client.post(
        "/addresses",
        headers=headers1,
        json=address_payload(),
    )

    address_id = create_response.json()["id"]

    register_user(
        client,
        "user2@example.com",
    )

    token2 = login_user(
        client,
        "user2@example.com",
    )

    headers2 = {
        "Authorization": f"Bearer {token2}",
    }

    response = client.patch(
        f"/addresses/{address_id}",
        headers=headers2,
        json={
            "city": "Mashhad",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Address not found"


def test_delete_address(
    client: TestClient,
    auth_headers: dict,
):
    create_response = client.post(
        "/addresses",
        headers=auth_headers,
        json=address_payload(),
    )

    address_id = create_response.json()["id"]

    response = client.delete(
        f"/addresses/{address_id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = client.get(
        f"/addresses/{address_id}",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_delete_default_assigns_another_address_as_default(
    client: TestClient,
    auth_headers: dict,
):
    first_response = client.post(
        "/addresses",
        headers=auth_headers,
        json=address_payload("Home"),
    )

    second_response = client.post(
        "/addresses",
        headers=auth_headers,
        json=address_payload("Work"),
    )

    first_id = first_response.json()["id"]
    second_id = second_response.json()["id"]

    response = client.delete(
        f"/addresses/{first_id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = client.get(
        f"/addresses/{second_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["is_default"] is True


def test_delete_last_address(
    client: TestClient,
    auth_headers: dict,
):
    create_response = client.post(
        "/addresses",
        headers=auth_headers,
        json=address_payload(),
    )

    address_id = create_response.json()["id"]

    response = client.delete(
        f"/addresses/{address_id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = client.get(
        "/addresses",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_address_requires_authentication(
    client: TestClient,
):
    response = client.get("/addresses")

    assert response.status_code == 401


@pytest.mark.parametrize(
    "field",
    [
        "title",
        "recipient_name",
        "phone",
        "province",
        "city",
        "address_line",
        "postal_code",
    ],
)
def test_create_address_requires_field(
    client: TestClient,
    auth_headers: dict,
    field: str,
):
    payload = address_payload()
    payload.pop(field)

    response = client.post(
        "/addresses",
        headers=auth_headers,
        json=payload,
    )

    assert response.status_code == 422