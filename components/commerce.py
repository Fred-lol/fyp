"""Shared, responsive catalogue presentation using native ordering controls."""
from html import escape
import streamlit as st
from components.seafood_images import seafood_card_image
from constants import LOW_STOCK_THRESHOLD, MIN_WHOLESALE_ORDER_KG

COMMERCE_CSS = """
<style>
.st-key-catalogue_grid[data-testid="stVerticalBlock"]{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr));gap:20px!important}
.st-key-catalogue_grid [class*="st-key-product_"]{height:100%;box-sizing:border-box;padding:18px!important;background:var(--aq-card)!important;border:1px solid var(--aq-border)!important;border-radius:12px!important;box-shadow:none!important;min-width:0}
.st-key-catalogue_grid [class*="st-key-product_"][data-testid="stVerticalBlock"]{display:flex!important;flex-direction:column!important;gap:10px!important;height:100%}
.st-key-catalogue_grid .aq-seafood-card-image{width:100%;overflow:hidden;line-height:0;height:auto!important;aspect-ratio:4/3;border:0!important;border-radius:8px!important}
.st-key-catalogue_grid .aq-seafood-card-image img{display:block;width:100%!important;max-height:none!important;height:100%!important;object-fit:cover!important}
.aq-product-heading{display:flex;gap:8px;align-items:flex-start;justify-content:space-between;margin-top:12px;min-height:52px}
.aq-product-heading h3{font-size:18px!important;line-height:1.4!important;margin:0!important;padding:0!important;color:var(--aq-text)!important;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.aq-stock-dot{font-size:12px;white-space:nowrap;color:var(--aq-muted);padding-top:4px}.aq-stock-dot::before{content:'●';color:var(--aq-teal);margin-right:4px}
.aq-product-meta{font-size:13px;line-height:1.5;color:var(--aq-muted);min-height:39px;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.aq-product-copy{font-size:14px;line-height:1.5;color:var(--aq-text);height:63px;margin:8px 0;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere}
.aq-product-pricing{display:flex;gap:8px;align-items:baseline;justify-content:space-between;flex-wrap:wrap;min-height:52px;border-bottom:1px solid var(--aq-border);padding-bottom:12px}
.aq-product-pricing strong{font-size:21px;color:var(--aq-text)}.aq-product-pricing small{font-size:13px;color:var(--aq-muted)}
.st-key-catalogue_grid [class*="st-key-product_"] [data-testid="stForm"]{margin-top:auto!important}
.st-key-catalogue_grid [class*="st-key-product_"] [data-testid="stNumberInput"]{margin-bottom:4px!important}
.st-key-catalogue_grid [data-testid="stForm"]{padding:0!important;border:0!important;background:transparent!important;box-shadow:none!important}
.st-key-catalogue_grid [data-testid="stFormSubmitButton"] button{box-shadow:none!important;background:var(--aq-primary-start)!important;color:var(--aq-on-primary)!important;min-height:44px!important}
.st-key-cart_panel{width:min(420px,calc(100vw - 64px));max-width:100%;padding:4px!important}
.st-key-cart_panel [class*="st-key-cart_line_"]{padding:16px 0!important;border-bottom:1px solid var(--aq-border)}
.aq-cart-line-title{display:flex;justify-content:space-between;gap:16px;font-size:15px;color:var(--aq-text)}
.aq-cart-line-price{font-size:13px;color:var(--aq-muted);margin:4px 0 10px}
.aq-cart-totals{display:flex;align-items:end;justify-content:space-between;gap:16px;padding:18px 0;color:var(--aq-text)}
.aq-cart-totals small{display:block;font-size:13px;color:var(--aq-muted)}.aq-cart-total-amount{font-size:24px;font-weight:700}
@media(max-width:1200px){.st-key-catalogue_grid[data-testid="stVerticalBlock"]{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:1000px){.st-key-catalogue_grid[data-testid="stVerticalBlock"]{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){.st-key-catalogue_grid[data-testid="stVerticalBlock"]{grid-template-columns:1fr}}
</style>
"""

def product_card(product, project_dir, on_add):
    """Render real product data and the existing form callback in a grid cell."""
    product_id = product['product_id']
    stock = float(product.get('stock_quantity') or 0)
    name = escape(product['product_name'])
    unit = escape(product.get('unit') or 'kg')
    status = 'Low stock' if stock <= LOW_STOCK_THRESHOLD else 'In stock'
    with st.container(key=f'product_{product_id}'):
        st.html(seafood_card_image(product, project_dir) + f'''
        <div class="aq-product-heading"><h3>{name}</h3><span class="aq-stock-dot">{status}</span></div>
        <div class="aq-product-meta">{escape(product.get('category') or 'Seafood')} &middot; Sold by {unit}</div>
        <p class="aq-product-copy">{escape(product.get('description') or 'Fresh seafood available for wholesale ordering.')}</p>
        <div class="aq-product-pricing"><div><strong>RM {float(product.get('unit_price') or 0):,.2f}</strong> <small>/ {unit}</small></div><small>{stock:g} {unit} available</small></div>''')
        current = min(max(float(st.session_state.cart.get(product_id, MIN_WHOLESALE_ORDER_KG)), MIN_WHOLESALE_ORDER_KG), stock)
        with st.form(f'cart_item_{product_id}', border=False):
            st.number_input(f'Quantity ({unit}, minimum {MIN_WHOLESALE_ORDER_KG:g})', min_value=MIN_WHOLESALE_ORDER_KG, max_value=stock, step=1.0, value=current, key=f'cart_quantity_{product_id}')
            st.form_submit_button('Add to cart', icon=':material/add_shopping_cart:', type='primary', width='stretch', on_click=on_add, args=(product_id, product['product_name']))
