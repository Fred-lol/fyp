from pathlib import Path

from components.commerce import COMMERCE_CSS
from components.seafood_images import seafood_card_image


def test_catalogue_and_details_use_contained_fixed_ratio_images():
    assert "aspect-ratio:4/3" in COMMERCE_CSS
    assert "object-fit:contain!important" in COMMERCE_CSS
    assert "object-fit:cover" not in COMMERCE_CSS

    image = seafood_card_image(
        {"product_name": "Test fish", "image_data": b"test-image", "image_mime_type": "image/png"},
        Path("."),
    )
    assert 'alt="Test fish"' in image
    assert "object-fit:contain" in image
    assert "loading=\"lazy\"" in image


def test_image_button_and_favorite_have_visible_focus_and_overlay_styles():
    assert "st-key-favorite_" in COMMERCE_CSS
    assert "z-index:5" in COMMERCE_CSS
    assert 'content:"View details"' not in COMMERCE_CSS
