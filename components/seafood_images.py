"""Consistent seafood image sources for catalogue tables and customer cards."""

from base64 import b64encode
from html import escape
from pathlib import Path
from urllib.parse import quote


_DEFAULT_SEAFOOD_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 160" role="img" aria-label="Seafood illustration">
  <defs><linearGradient id="sea" x1="0" x2="1"><stop stop-color="#087ead"/><stop offset="1" stop-color="#13b9bb"/></linearGradient></defs>
  <rect width="240" height="160" rx="18" fill="#e8fbf8"/>
  <path d="M38 96c28-45 90-58 133-17l31-21-7 36 7 36-31-20c-43 40-105 27-133-14Z" fill="url(#sea)"/>
  <circle cx="82" cy="77" r="6" fill="#fff"/><circle cx="83" cy="78" r="2.5" fill="#063b63"/>
  <path d="M17 132c28-10 54-10 80 0s52 10 80 0 45-10 63 0" fill="none" stroke="#6cd9d5" stroke-width="7" stroke-linecap="round"/>
  <text x="120" y="148" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" font-weight="700" fill="#063b63">AquaLoad Seafood</text>
</svg>
""".strip()

DEFAULT_SEAFOOD_IMAGE = f"data:image/svg+xml;charset=utf-8,{quote(_DEFAULT_SEAFOOD_SVG)}"


def seafood_image_source(product: dict, project_dir: Path) -> str:
    """Return an uploaded image, local legacy image, or a friendly default image."""
    image_data = product.get("image_data")
    if image_data:
        mime_type = product.get("image_mime_type") or "image/png"
        return f"data:{mime_type};base64,{b64encode(bytes(image_data)).decode('ascii')}"
    image_path = product.get("image_path")
    if image_path:
        candidate = project_dir / image_path
        if candidate.is_file():
            extension = candidate.suffix.lower().lstrip(".") or "png"
            mime_type = "image/jpeg" if extension == "jpg" else f"image/{extension}"
            return f"data:{mime_type};base64,{b64encode(candidate.read_bytes()).decode('ascii')}"
    return DEFAULT_SEAFOOD_IMAGE


def seafood_card_image(product: dict, project_dir: Path, height: int = 260) -> str:
    """Return a fixed, crop-safe image frame for seafood catalogue cards.

    Uploaded images are stored with their product in PostgreSQL.  Each image
    keeps its own proportions: it is never cropped and the card does not add
    empty letterbox space around it.
    """
    source = escape(seafood_image_source(product, project_dir), quote=True)
    name = escape(str(product.get("product_name") or "Seafood"), quote=True)
    return f'''<div class="aq-seafood-card-image">
      <img src="{source}" alt="{name}" loading="eager" decoding="async" style="max-height:{height}px" />
    </div>'''
