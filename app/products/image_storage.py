import os
import re
from pathlib import Path
from uuid import uuid4


PRODUCT_IMAGE_DIR = Path(os.getenv("PRODUCT_IMAGE_DIR", "uploads/products"))
PRODUCT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
MAX_PRODUCT_IMAGE_BYTES = 5 * 1024 * 1024

_CONTENT_TYPES = {
    "image/jpeg": (".jpg", lambda data: data.startswith(b"\xff\xd8\xff")),
    "image/png": (".png", lambda data: data.startswith(b"\x89PNG\r\n\x1a\n")),
    "image/webp": (
        ".webp",
        lambda data: len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP",
    ),
}
_STORED_FILENAME = re.compile(r"^[0-9a-f]{32}\.(?:jpg|png|webp)$")


def store_product_image(contents: bytes, content_type: str | None) -> tuple[str, Path]:
    image_format = _CONTENT_TYPES.get(content_type or "")
    if image_format is None or not image_format[1](contents):
        raise ValueError("فقط تصویر معتبر JPG، PNG یا WebP قابل بارگذاری است.")

    filename = f"{uuid4().hex}{image_format[0]}"
    destination = PRODUCT_IMAGE_DIR / filename
    destination.write_bytes(contents)
    return f"/uploads/products/{filename}", destination


def delete_stored_product_image(image_url: str | None) -> None:
    if not image_url:
        return

    filename = image_url.rsplit("/", 1)[-1]
    if _STORED_FILENAME.fullmatch(filename):
        (PRODUCT_IMAGE_DIR / filename).unlink(missing_ok=True)
