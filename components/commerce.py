"""Compact catalogue cards and a separate ordering details view."""
from html import escape
from urllib.parse import urlencode
import streamlit as st
from components.seafood_images import seafood_card_image
from constants import LOW_STOCK_THRESHOLD, MIN_WHOLESALE_ORDER_KG

COMMERCE_CSS = """
<style>
.st-key-catalogue_grid[data-testid="stVerticalBlock"]{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr));gap:20px!important}
.st-key-catalogue_grid [class*="st-key-product_"]{height:100%;box-sizing:border-box;padding:14px!important;background:var(--aq-card)!important;border:1px solid var(--aq-border)!important;border-radius:12px!important;box-shadow:none!important;min-width:0}
.st-key-catalogue_grid [class*="st-key-product_"][data-testid="stVerticalBlock"]{display:flex!important;flex-direction:column!important;gap:10px!important;height:100%}
.aq-catalogue-link{display:block;color:var(--aq-text)!important;text-decoration:none!important;height:100%}.aq-catalogue-link:hover .aq-product-heading h3{color:var(--aq-teal)!important}.aq-catalogue-link:focus-visible{outline:3px solid var(--aq-teal);outline-offset:4px;border-radius:8px}
.aq-detail-image .aq-seafood-card-image{width:100%;height:320px;border-radius:10px;overflow:hidden;line-height:0}.aq-detail-image img{display:block;width:100%;height:100%;max-height:none!important;object-fit:cover}.aq-detail-meta{color:var(--aq-muted);margin:8px 0 16px}.aq-detail-description{line-height:1.65;color:var(--aq-text)}.aq-detail-price{font-size:25px;font-weight:750;color:var(--aq-text);margin:18px 0 10px}.aq-detail-stock{color:var(--aq-teal);font-weight:650}
.st-key-catalogue_grid .aq-seafood-card-image{width:100%;overflow:hidden;line-height:0;height:auto!important;aspect-ratio:4/3;border:0!important;border-radius:8px!important}
.st-key-catalogue_grid .aq-seafood-card-image img{display:block;width:100%!important;max-height:none!important;height:100%!important;object-fit:cover!important}
.aq-product-heading{display:flex;gap:8px;align-items:flex-start;justify-content:space-between;margin-top:12px;min-height:52px}
.aq-product-heading h3{font-size:18px!important;line-height:1.4!important;margin:0!important;padding:0!important;color:var(--aq-text)!important;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.aq-stock-dot{font-size:12px;white-space:nowrap;color:var(--aq-muted);padding-top:4px}.aq-stock-dot::before{content:'●';color:var(--aq-teal);margin-right:4px}
.aq-product-pricing{display:flex;gap:8px;align-items:baseline;justify-content:space-between;flex-wrap:wrap;min-height:52px;border-bottom:1px solid var(--aq-border);padding-bottom:12px}
.aq-product-pricing strong{font-size:21px;color:var(--aq-text)}.aq-product-pricing small{font-size:13px;color:var(--aq-muted)}
.st-key-cart_panel{width:min(420px,calc(100vw - 64px));max-width:100%;padding:4px!important}
.st-key-cart_panel [class*="st-key-cart_line_"]{padding:16px 0!important;border-bottom:1px solid var(--aq-border)}
.aq-cart-line-title{display:flex;justify-content:space-between;gap:16px;font-size:15px;color:var(--aq-text)}
.aq-cart-line-price{font-size:13px;color:var(--aq-muted);margin:4px 0 10px}
.aq-cart-totals{display:flex;align-items:end;justify-content:space-between;gap:16px;padding:18px 0;color:var(--aq-text)}
.aq-cart-totals small{display:block;font-size:13px;color:var(--aq-muted)}.aq-cart-total-amount{font-size:24px;font-weight:700}
@media(max-width:1200px){.st-key-catalogue_grid[data-testid="stVerticalBlock"]{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:1000px){.st-key-catalogue_grid[data-testid="stVerticalBlock"]{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){.st-key-catalogue_grid[data-testid="stVerticalBlock"]{grid-template-columns:1fr}}
@media(max-width:700px){.aq-detail-image .aq-seafood-card-image{height:260px}}
</style>
"""

def product_card(product, project_dir, *, search="", category="All"):
    """Render a clickable catalogue card using real product data."""
    product_id = product['product_id']
    stock = float(product.get('stock_quantity') or 0)
    name = escape(product['product_name'])
    unit = escape(product.get('unit') or 'kg')
    status = 'Low stock' if stock <= LOW_STOCK_THRESHOLD else 'In stock'
    href = '?' + urlencode({'product': product_id, 'search': search, 'category': category})
    with st.container(key=f'product_{product_id}'):
        st.html(f'''<a class="aq-catalogue-link" href="{escape(href, quote=True)}" target="_self" aria-label="View details for {escape(product['product_name'], quote=True)}">
        {seafood_card_image(product, project_dir)}
        <div class="aq-product-heading"><h3>{name}</h3></div>
        <div class="aq-product-pricing"><strong>RM {float(product.get('unit_price') or 0):,.2f} <small>/ {unit}</small></strong></div>
        <div class="aq-stock-dot">{status} &middot; {stock:g} {unit} available</div></a>''')


def product_details(product, project_dir, on_add):
    """Render the complete information for a selected seafood item."""
    stock = float(product.get('stock_quantity') or 0)
    unit = escape(product.get('unit') or 'kg')
    name = escape(product['product_name'])
    price = float(product.get('unit_price') or 0)
    image_col, info_col = st.columns(2, gap="large")
    with image_col:
        st.html(f'<div class="aq-detail-image">{seafood_card_image(product, project_dir)}</div>')
    with info_col:
        st.html(f'''<h2>{name}</h2><div class="aq-detail-meta">{escape(product.get('category') or 'Seafood')}</div>
        <p class="aq-detail-description">{escape(product.get('description') or 'Fresh seafood available for wholesale ordering.')}</p>
        <div class="aq-detail-price">RM {price:,.2f} / {unit}</div>
        <div class="aq-detail-stock">{stock:g} {unit} available</div><p>Minimum order: {MIN_WHOLESALE_ORDER_KG:g} {unit}</p>''')
        product_id = product['product_id']
        quantity = st.number_input(
            f"Quantity ({unit})", min_value=MIN_WHOLESALE_ORDER_KG, max_value=stock, step=1.0,
            value=min(max(float(st.session_state.cart.get(product_id, MIN_WHOLESALE_ORDER_KG)), MIN_WHOLESALE_ORDER_KG), stock),
            key=f"cart_quantity_{product_id}",
        )
        st.html(f'<p class="aq-detail-price">Subtotal: RM {float(quantity) * price:,.2f}</p>')
        st.button("Add to Cart", icon=":material/add_shopping_cart:", type="primary", on_click=on_add,
                  args=(product_id, product["product_name"]), key="detail_add_to_cart")
