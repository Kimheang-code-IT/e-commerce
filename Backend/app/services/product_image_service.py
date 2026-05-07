import base64
import re
import uuid
from pathlib import Path
from app.core.config import settings

DATA_URL_RE = re.compile(
    r"^data:image/(png|jpeg|jpg|gif|webp);base64,(.+)$",
    re.IGNORECASE | re.DOTALL,
)


def upload_root() -> Path:
    root = Path(__file__).resolve().parent.parent.parent / "uploads"
    root.mkdir(parents=True, exist_ok=True)
    return root


def delete_stored_file_if_local(stored: str | None) -> None:
    if not stored or not stored.startswith("/uploads/products/"):
        return
    rel = stored.removeprefix("/uploads/")
    path = upload_root() / rel
    try:
        if path.is_file():
            path.unlink()
    except OSError:
        pass


def save_data_url_as_file(data_url: str, product_id: int) -> str:
    raw = data_url.strip()
    if not raw.startswith("data:image/"):
        raise ValueError("Invalid image format")

    m = DATA_URL_RE.match(raw)
    if not m:
        raise ValueError("Invalid image data")

    ext = m.group(1).lower()
    if ext == "jpeg":
        ext = "jpg"
    image_bytes = base64.b64decode(m.group(2), validate=True)
    max_bytes = 3 * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise ValueError("Image too large")

    products_dir = upload_root() / "products"
    products_dir.mkdir(parents=True, exist_ok=True)
    filename = f"p_{product_id}_{uuid.uuid4().hex[:12]}.{ext}"
    path = products_dir / filename
    path.write_bytes(image_bytes)
    return f"/uploads/products/{filename}"


def normalize_stored_image(value: str | None, product_id: int, previous_stored: str | None) -> str:
    """Persist incoming image value; returns path/url to store in DB."""
    if value is None:
        return previous_stored or ""

    v = value.strip()
    if not v:
        delete_stored_file_if_local(previous_stored)
        return ""

    if v.startswith("data:image/"):
        new_path = save_data_url_as_file(v, product_id)
        if previous_stored and previous_stored != new_path:
            delete_stored_file_if_local(previous_stored)
        return new_path

    if v.startswith(("http://", "https://", "/uploads/")):
        return v

    raise ValueError("Unsupported image value")


def public_image_url(stored: str | None) -> str:
    if not stored:
        return ""
    if stored.startswith(("http://", "https://", "data:")):
        return stored
    base = (settings.file_base_url or "").rstrip("/")
    path = stored if stored.startswith("/") else f"/{stored}"
    return f"{base}{path}" if base else path
