"""Compact seafood catalogue cards and a separate detail presentation."""
from html import escape

import streamlit as st

from components.seafood_images import seafood_card_image
from constants import LOW_STOCK_THRESHOLD, MIN_WHOLESALE_ORDER_KG


COMMERCE_CSS = """
<style>
.st-key-catalogue_grid[data-testid="stVerticalBlock"]{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px!important;align-items:stretch}
.st-key-catalogue_grid [class*="st-key-product_"][data-testid="stVerticalBlock"]{position:relative;display:flex!important;flex-direction:column!important;gap:10px!important;height:100%;box-sizing:border-box;padding:12px!important;background:var(--aq-card)!important;border:1px solid var(--aq-border)!important;border-radius:13px!important;box-shadow:0 6px 18px rgba(8,46,75,.055)!important;min-width:0;transition:border-color .18s ease,box-shadow .18s ease,transform .18s ease}
.st-key-catalogue_grid [class*="st-key-product_"][data-testid="stVerticalBlock"]:hover{border-color:color-mix(in srgb,var(--aq-teal) 55%,var(--aq-border))!important;box-shadow:0 12px 26px rgba(8,46,75,.10)!important;transform:translateY(-2px)}
.st-key-catalogue_grid .aq-product-image-frame{width:100%;margin:0!important}
.st-key-catalogue_grid .aq-product-image-frame .aq-seafood-card-image{width:100%;aspect-ratio:4/3;height:auto;border:1px solid rgba(8,46,75,.12);border-radius:9px;overflow:hidden;line-height:0;background:#f2f5f6}
.st-key-catalogue_grid .aq-product-image-frame img{display:block;width:100%;height:100%;max-height:none!important;object-fit:contain!important;object-position:center;background:#f2f5f6}
.st-key-catalogue_grid [class*="st-key-favorite_"]{position:absolute!important;top:17px;right:17px;z-index:4;width:36px;height:36px;margin:0!important}
.st-key-catalogue_grid [class*="st-key-favorite_"] button{width:36px!important;height:36px!important;min-height:36px!important;padding:0!important;border-radius:50%!important;background:#fff!important;border:1px solid rgba(8,46,75,.16)!important;color:#b42345!important;box-shadow:0 2px 8px rgba(8,46,75,.2)!important;position:relative!important;z-index:5!important}
.st-key-catalogue_grid [class*="st-key-favorite_"] button *{color:#b42345!important;fill:currentColor!important;stroke:currentColor!important}
.st-key-catalogue_favorites_filter button{width:100%!important;min-height:40px!important;padding:0 12px!important;border:1px solid var(--aq-border)!important;border-radius:999px!important;background:var(--aq-card)!important;box-shadow:none!important;color:var(--aq-text)!important;white-space:nowrap!important;font-size:13px!important;font-weight:650!important}
.st-key-catalogue_favorites_filter button p{font-size:13px!important;line-height:1.15!important;margin:0!important;white-space:nowrap!important}
.st-key-catalogue_favorites_filter button [data-testid="stIconMaterial"]{font-size:19px!important;line-height:1!important}
.st-key-catalogue_favorites_active .st-key-catalogue_favorites_filter button{background:color-mix(in srgb,#e11d48 9%,var(--aq-card))!important;border-color:color-mix(in srgb,#e11d48 45%,var(--aq-border))!important}
.st-key-catalogue_favorites_active .st-key-catalogue_favorites_filter button [data-testid="stIconMaterial"]{color:#e11d48!important;-webkit-text-fill-color:#e11d48!important}
.st-key-catalogue_grid [class*="st-key-favorite_"] button [data-testid="stIconMaterial"]{font-size:20px!important;color:#e11d48!important}
.aq-product-name{min-height:2.7em;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;color:var(--aq-text);font-size:16px;font-weight:750;line-height:1.35}
.aq-product-pricing{display:flex;align-items:baseline;gap:5px;color:var(--aq-text)}.aq-product-pricing strong{font-size:19px;font-weight:800}.aq-product-pricing small{font-size:12px;color:var(--aq-muted);font-weight:500}
.aq-product-stock{margin-top:auto;display:flex;align-items:center;gap:7px;color:var(--aq-muted);font-size:12px;line-height:1.4}.aq-product-stock:before{content:"";width:8px;height:8px;flex:none;border-radius:50%;background:#0b9b78}.aq-product-stock.aq-low:before{background:#dc9b28}
.st-key-catalogue_grid [class*="st-key-view_details_"]{margin-top:2px}.st-key-catalogue_grid [class*="st-key-view_details_"] button{min-height:38px!important;border-radius:8px!important}
.aq-detail-layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:clamp(24px,4vw,52px);align-items:start}.aq-detail-image{position:sticky;top:20px}.aq-detail-image .aq-seafood-card-image{width:100%;aspect-ratio:4/3;height:auto;border-radius:12px;overflow:hidden;line-height:0;background:#f2f5f6;border:1px solid rgba(8,46,75,.12)}.aq-detail-image img{display:block;width:100%;height:100%;max-height:none!important;object-fit:contain!important;object-position:center;background:#f2f5f6}.aq-detail-title-row{display:flex;align-items:flex-start;justify-content:space-between;gap:14px}.aq-detail-title-row h2{margin:0;color:var(--aq-text)}.aq-detail-meta{color:var(--aq-muted);margin:8px 0 16px}.aq-detail-description{min-height:4.5em;line-height:1.65;color:var(--aq-text);white-space:pre-line}.aq-detail-price{font-size:24px;font-weight:800;color:var(--aq-text);margin:18px 0 8px}.aq-detail-stock{color:var(--aq-teal);font-weight:700}.aq-detail-subtotal{font-size:19px;font-weight:750;color:var(--aq-text);margin:14px 0}
.st-key-detail_favorite button{min-height:38px!important;padding:0 12px!important;border-radius:999px!important}
.st-key-cart_panel{width:min(420px,calc(100vw - 64px));max-width:100%;padding:4px!important}.st-key-cart_panel [class*="st-key-cart_line_"]{padding:16px 0!important;border-bottom:1px solid var(--aq-border)}
.aq-cart-line-title{display:flex;justify-content:space-between;gap:16px;font-size:15px;color:var(--aq-text)}.aq-cart-totals{display:flex;align-items:end;justify-content:space-between;gap:16px;padding:18px 0;color:var(--aq-text)}.aq-cart-total-amount{font-size:24px;font-weight:700}
@media(max-width:1100px){.st-key-catalogue_grid[data-testid="stVerticalBlock"]{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:800px){.st-key-catalogue_grid[data-testid="stVerticalBlock"]{grid-template-columns:repeat(2,minmax(0,1fr))}.aq-detail-layout{grid-template-columns:1fr}.aq-detail-image{position:static}}
@media(max-width:520px){.st-key-catalogue_grid[data-testid="stVerticalBlock"]{grid-template-columns:1fr}.st-key-catalogue_grid [class*="st-key-product_"][data-testid="stVerticalBlock"]{padding:12px!important}.aq-detail-layout{gap:18px}}
</style>
"""


def product_card(product, project_dir, on_open, *, is_favorite=False, on_favorite=None):
    """Render a compact card. Its image and explicit action both open details."""
    product_id = int(product["product_id"])
    name = escape(str(product["product_name"]))
    stock = float(product.get("stock_quantity") or 0)
    unit = escape(product.get("unit") or "kg")
    low = stock <= LOW_STOCK_THRESHOLD
    icon = "♥" if is_favorite else "♡"
    with st.container(key=f"product_{product_id}"):
        st.button(
            icon,
            key=f"favorite_{product_id}",
            type="tertiary",
            help="Remove from favorites" if is_favorite else "Add to favorites",
            on_click=on_favorite,
            args=(product_id,),
        )
        st.html(f'<div class="aq-product-image-frame">{seafood_card_image(product, project_dir)}</div>')
        st.html(f'<div class="aq-product-name">{name}</div>')
        st.html(f'<div class="aq-product-pricing"><strong>RM {float(product.get("unit_price") or 0):,.2f}</strong><small>/ {unit}</small></div>')
        stock_class = " aq-low" if low else ""
        stock_text = "Low stock" if low else "In stock"
        st.html(f'<div class="aq-product-stock{stock_class}">{stock_text} &middot; {stock:g} {unit} available</div>')
        st.button(
            "View Details",
            key=f"view_details_{product_id}",
            on_click=on_open,
            args=(product_id,),
            use_container_width=True,
        )


def product_details(product, project_dir, on_add, *, is_favorite=False, on_favorite=None):
    """Render full product information while staying on the authenticated route."""
    stock = float(product.get("stock_quantity") or 0)
    unit = escape(product.get("unit") or "kg")
    name = escape(product["product_name"])
    price = float(product.get("unit_price") or 0)
    product_id = int(product["product_id"])
    quantity_key = f"cart_quantity_{product_id}"
    if quantity_key not in st.session_state:
        st.session_state[quantity_key] = min(
            max(float(st.session_state.cart.get(product_id, MIN_WHOLESALE_ORDER_KG)), MIN_WHOLESALE_ORDER_KG),
            stock,
        )

    image_col, info_col = st.columns([1, 1], gap="large", vertical_alignment="top")
    with image_col:
        st.html(f'<div class="aq-detail-image">{seafood_card_image(product, project_dir)}</div>')
    with info_col:
        st.html(f'<div class="aq-detail-title-row"><h2>{name}</h2></div>')
        st.button(
            "Saved to favorites" if is_favorite else "Add to favorites",
            icon=":material/favorite:" if is_favorite else ":material/favorite_border:",
            key="detail_favorite",
            type="tertiary",
            help="Remove from favorites" if is_favorite else "Add to favorites",
            on_click=on_favorite,
            args=(product_id,),
        )
        st.html(
            f'<div class="aq-detail-meta">{escape(product.get("category") or "Seafood")}</div>'
            f'<p class="aq-detail-description">{escape(product.get("description") or "Fresh seafood available for wholesale ordering.")}</p>'
            f'<div class="aq-detail-price">RM {price:,.2f} / {unit}</div>'
            f'<div class="aq-detail-stock">{stock:g} {unit} available</div>'
            f'<p>Minimum order: {MIN_WHOLESALE_ORDER_KG:g} {unit}</p>'
        )
        quantity = st.number_input(
            f"Quantity ({unit})",
            min_value=MIN_WHOLESALE_ORDER_KG,
            max_value=stock,
            step=1.0,
            key=quantity_key,
        )
        st.html(f'<div class="aq-detail-subtotal">Subtotal: RM {float(quantity) * price:,.2f}</div>')
        st.button(
            "Add to Cart",
            icon=":material/add_shopping_cart:",
            type="primary",
            on_click=on_add,
            args=(product_id, product["product_name"]),
            key="detail_add_to_cart",
            use_container_width=True,
        )
