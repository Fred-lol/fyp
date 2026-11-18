"""Customer seafood catalogue and cart workspace."""

import sys
from html import escape
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.navigation import customer_sidebar
from components.seafood_images import seafood_card_image
from components.theme import apply_theme, page_header
from constants import LOW_STOCK_THRESHOLD, MIN_WHOLESALE_ORDER_KG
from services.order_service import list_products, product_categories
from services.payment_service import checkout_summary


bootstrap_app()
st.set_page_config(page_title="Order Seafood | AquaLoad", page_icon="🐟", layout="wide")
apply_theme()
customer_sidebar()

st.html("""
<style>
[data-testid="stMain"] [class*="st-key-seafood-card-"]{min-height:470px!important;padding:12px!important;border-radius:14px!important;background:var(--aq-card)!important;border:1px solid var(--aq-border)!important;box-shadow:0 2px 8px rgba(3,28,53,.045)!important}
[data-testid="stMain"] [class*="st-key-seafood-card-"] [data-testid="stVerticalBlock"]{gap:8px!important}
[data-testid="stMain"] [class*="st-key-seafood-card-"] [data-testid="stForm"]{padding:0!important;background:transparent!important;border:0!important;box-shadow:none!important}
[data-testid="stMain"] [class*="st-key-seafood-card-"] .aq-seafood-card-image{height:170px!important}
[data-testid="stMain"] [class*="st-key-seafood-card-"] h4{margin:2px 0 0!important;font-size:1.08rem!important;line-height:1.25!important}
[data-testid="stMain"] [class*="st-key-seafood-card-"] [data-testid="stCaptionContainer"] p{margin:0!important;font-size:.78rem!important}
.aq-product-description{min-height:2.7rem!important;margin:0!important;color:var(--aq-muted)!important;font-size:.84rem!important;line-height:1.5!important;display:-webkit-box!important;-webkit-box-orient:vertical!important;-webkit-line-clamp:2!important;overflow:hidden!important}
.aq-product-price{margin:0!important;color:var(--aq-navy)!important;font-size:1rem!important;font-weight:800!important}
.aq-stock-banner{margin:0!important;padding:7px 10px!important;border-radius:8px!important;font-size:.78rem!important;font-weight:750!important;line-height:1.3!important}
.aq-stock-banner.available{background:var(--aq-status-success-bg)!important;color:var(--aq-status-success-text)!important;border:1px solid color-mix(in srgb,var(--aq-status-success-text) 32%,transparent)!important}.aq-stock-banner.low{background:var(--aq-status-warning-bg)!important;color:var(--aq-status-warning-text)!important;border:1px solid color-mix(in srgb,var(--aq-status-warning-text) 32%,transparent)!important}.aq-stock-banner.out{background:var(--aq-status-danger-bg)!important;color:var(--aq-status-danger-text)!important;border:1px solid color-mix(in srgb,var(--aq-status-danger-text) 32%,transparent)!important}
[data-testid="stMain"] [class*="st-key-seafood-card-"] .stNumberInput [data-baseweb="input"]{min-height:40px!important}[data-testid="stMain"] [class*="st-key-seafood-card-"] .stNumberInput [data-baseweb="input"] input,[data-testid="stMain"] [class*="st-key-seafood-card-"] .stNumberInput [data-baseweb="input"] button{height:40px!important}[data-testid="stMain"] [class*="st-key-seafood-card-"] [data-testid="stFormSubmitButton"]{margin-top:2px!important}[data-testid="stMain"] [class*="st-key-seafood-card-"] [data-testid="stFormSubmitButton"] button{min-height:41px!important}
@media(max-width:900px){[data-testid="stMain"] [class*="st-key-seafood-card-"]{min-height:0!important}[data-testid="stMain"] [class*="st-key-seafood-card-"] .aq-seafood-card-image{height:190px!important}}
</style>
""")

page_header("Order Seafood", "Browse the current wholesale catalogue, add items to your cart, then review payment.", "Customer Ordering")

if "cart" not in st.session_state:
    st.session_state.cart = {}


def _catalogue_products(search: str, category: str) -> list[dict]:
    """Use real inventory, including unavailable products shown as disabled."""
    return list_products(search, category, "All")


def _change_cart_quantity(product_id: int) -> None:
    quantity = float(st.session_state[f"cart_popover_quantity_{product_id}"])
    if quantity >= MIN_WHOLESALE_ORDER_KG:
        st.session_state.cart[product_id] = quantity
        st.session_state[f"cart_quantity_{product_id}"] = quantity


def _add_product_to_cart(product_id: int) -> None:
    quantity = float(st.session_state[f"cart_quantity_{product_id}"])
    if quantity >= MIN_WHOLESALE_ORDER_KG:
        st.session_state.cart[product_id] = quantity
        st.session_state[f"cart_popover_quantity_{product_id}"] = quantity


def _stock_state(product: dict) -> tuple[str, str, bool]:
    stock = float(product.get("stock_quantity") or 0)
    unit = product.get("unit") or "kg"
    available = product.get("availability_status") == "Available" and stock >= MIN_WHOLESALE_ORDER_KG
    if not available:
        return "out", "Out of stock · unavailable", False
    if stock <= LOW_STOCK_THRESHOLD:
        return "low", f"Low stock · {stock:g} {unit} available", True
    return "available", f"In stock · {stock:g} {unit} available", True


@st.fragment
def ordering_workspace() -> None:
    filters, category_filter, cart_action = st.columns([2.2, 1, .58], vertical_alignment="bottom")
    with filters:
        search = st.text_input("Search seafood", placeholder="Search by seafood name")
    with category_filter:
        category = st.selectbox("Category", ["All"] + product_categories())
    with cart_action:
        cart_summary = checkout_summary(list(st.session_state.cart.items()))
        with st.popover(f"Cart ({len(cart_summary['items'])})", icon=":material/shopping_cart:", help="Review cart", use_container_width=True):
            st.subheader("Your Cart", anchor=False)
            if not cart_summary["items"]:
                st.info("Your cart is empty. Add seafood to begin your order.")
            else:
                for line in cart_summary["items"]:
                    st.markdown(f"**{line['product_name']}**")
                    st.caption(f"RM {line['unit_price']:,.2f} / {line['unit']} · Available: {line['stock_quantity']:g} {line['unit']}")
                    quantity_col, remove_col = st.columns([5, .75], vertical_alignment="bottom")
                    with quantity_col:
                        st.number_input(
                            f"Quantity for {line['product_name']} ({line['unit']})", min_value=MIN_WHOLESALE_ORDER_KG,
                            max_value=max(MIN_WHOLESALE_ORDER_KG, float(line["stock_quantity"])),
                            value=max(MIN_WHOLESALE_ORDER_KG, min(float(line["quantity"]), float(line["stock_quantity"]))), step=1.0,
                            key=f"cart_popover_quantity_{line['product_id']}", on_change=_change_cart_quantity, args=(line["product_id"],),
                        )
                    with remove_col:
                        if st.button(":material/delete:", key=f"remove_cart_item_{line['product_id']}", help=f"Remove {line['product_name']} from cart", type="tertiary"):
                            st.session_state.cart.pop(line["product_id"], None)
                            st.session_state.pop(f"cart_popover_quantity_{line['product_id']}", None)
                            st.session_state.pop(f"cart_quantity_{line['product_id']}", None)
                            st.toast(f"{line['product_name']} removed from cart.")
                            st.rerun(scope="fragment")
                st.divider()
                st.markdown(f"**Total weight:** {cart_summary['total_weight_kg']:g} kg")
                st.markdown(f"### RM {cart_summary['total_amount']:,.2f}")
                if st.button("Proceed to payment", type="primary", use_container_width=True, key="cart_proceed_payment"):
                    invalid = [line for line in cart_summary["items"] if line["availability_status"] != "Available" or line["quantity"] < MIN_WHOLESALE_ORDER_KG or line["quantity"] > line["stock_quantity"] + 1e-9]
                    if invalid:
                        st.error("One or more cart items are no longer available. Review their quantity before payment.")
                    else:
                        st.session_state.checkout_cart = list(st.session_state.cart.items())
                        st.switch_page("pages/payment.py")

    products = _catalogue_products(search, category)
    if not products:
        st.info("No seafood matches your search or selected category.")
        return

    columns = st.columns(4, gap="small")
    for index, product in enumerate(products):
        product_id = product["product_id"]
        stock = float(product.get("stock_quantity") or 0)
        stock_class, stock_message, can_order = _stock_state(product)
        with columns[index % 4]:
            with st.container(border=True, key=f"seafood-card-{product_id}"):
                st.html(seafood_card_image(product, PROJECT_DIR, height=170))
                st.markdown(f"#### {product['product_name']}")
                st.caption(f"{product.get('category') or 'Seafood'} · Sold by {product.get('unit') or 'kg'}")
                st.html(f'<p class="aq-product-description">{escape(product.get("description") or "Fresh seafood available for wholesale ordering.")}</p>')
                st.html(f'<p class="aq-product-price">RM {float(product.get("unit_price") or 0):,.2f} / {product.get("unit") or "kg"}</p>')
                st.html(f'<p class="aq-stock-banner {stock_class}">{stock_message}</p>')
                if can_order:
                    current = min(max(float(st.session_state.cart.get(product_id, MIN_WHOLESALE_ORDER_KG)), MIN_WHOLESALE_ORDER_KG), stock)
                    in_cart = product_id in st.session_state.cart
                    with st.form(f"cart_item_{product_id}", border=False):
                        st.number_input(f"Quantity ({product.get('unit') or 'kg'})", min_value=MIN_WHOLESALE_ORDER_KG, max_value=stock, step=1.0, value=current, key=f"cart_quantity_{product_id}")
                        st.caption(f"Minimum wholesale order: {MIN_WHOLESALE_ORDER_KG:g} kg")
                        saved = st.form_submit_button("Add to cart", icon=":material/add_shopping_cart:", type="primary", use_container_width=True, on_click=_add_product_to_cart, args=(product_id,))
                    if saved:
                        st.toast(f"{product['product_name']} {'quantity updated' if in_cart else 'added to cart'}.", icon="✅")
                else:
                    st.button("Unavailable", disabled=True, use_container_width=True, key=f"unavailable_{product_id}")


ordering_workspace()
