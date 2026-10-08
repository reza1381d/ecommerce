from decimal import Decimal

from app.products.models import Product
from tests.admin_helpers import auth_headers, make_user


def make_product(db):
    product = Product(
        name="Image test product",
        description=None,
        price=Decimal("100"),
        stock=5,
        reserved_stock=0,
        is_active=True,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def test_admin_can_upload_and_remove_product_image(client, db, monkeypatch, tmp_path):
    admin = make_user(db, email="admin@example.com", role="admin")
    product = make_product(db)
    stored_path = tmp_path / "image.png"
    deleted_urls = []

    def store_image(contents, content_type):
        assert contents.startswith(b"\x89PNG\r\n\x1a\n")
        assert content_type == "image/png"
        stored_path.write_bytes(contents)
        return "/uploads/products/image.png", stored_path

    monkeypatch.setattr("app.products.router.store_product_image", store_image)
    monkeypatch.setattr(
        "app.products.router.delete_stored_product_image",
        lambda url: deleted_urls.append(url) if url else None,
    )

    response = client.post(
        f"/products/{product.id}/image",
        headers=auth_headers(admin),
        files={"file": ("image.png", b"\x89PNG\r\n\x1a\ncontents", "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["image_url"] == "/uploads/products/image.png"
    assert stored_path.exists()

    response = client.delete(f"/products/{product.id}/image", headers=auth_headers(admin))
    assert response.status_code == 200
    assert response.json()["image_url"] is None
    assert deleted_urls == ["/uploads/products/image.png"]


def test_product_image_upload_rejects_invalid_type_and_requires_admin(client, db):
    admin = make_user(db, email="admin@example.com", role="admin")
    customer = make_user(db)
    product = make_product(db)

    invalid = client.post(
        f"/products/{product.id}/image",
        headers=auth_headers(admin),
        files={"file": ("image.png", b"not a png", "image/png")},
    )
    assert invalid.status_code == 415

    forbidden = client.post(
        f"/products/{product.id}/image",
        headers=auth_headers(customer),
        files={"file": ("image.png", b"data", "image/png")},
    )
    assert forbidden.status_code == 403

