import sys
from html import escape
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.theme import apply_theme, page_header
from components.navigation import customer_sidebar
from components.seafood_images import seafood_card_image
from services.order_service import list_products, product_categories
from services.payment_service import checkout_summary
from constants import LOW_STOCK_THRESHOLD, MIN_WHOLESALE_ORDER_KG, SEAFOOD_CATEGORIES

bootstrap_app()
st.set_page_config(page_title="Order Seafood | AquaLoad", page_icon="🐟", layout="wide")
apply_theme(); customer_sidebar()
st.html("""
<style>
/* Compact marketplace catalogue: remove the artificial 850px card height,
   nested form surface and repeated large alert panels. */
[data-testid="stMain"] [class*="st-key-seafood-card-"]{min-height:0!important}
[data-testid="stMain"] [class*="st-key-seafood-card-"] [data-testid="stVerticalBlock"]{gap:.42rem!important}
[data-testid="stMain"] [class*="st-key-seafood-card-"] [data-testid="stForm"]{background:transparent!important;border:0!important;box-shadow:none!important;padding:0!important}
[data-testid="stMain"] [class*="st-key-seafood-card-"] .aq-seafood-card-image img{max-height:160px!important}
.aq-product-description{margin:0!important;color:var(--aq-text)!important;font-size:.82rem!important;line-height:1.45!important;display:-webkit-box!important;-webkit-line-clamp:2!important;-webkit-box-orient:vertical!important;overflow:hidden!important;min-height:2.38rem}
.aq-product-price{margin:0!important;color:var(--aq-navy)!important;font-size:.95rem!important;font-weight:800!important}
.aq-stock-banner{margin:0!important;padding:8px 10px!important;border-radius:8px!important;font-size:.78rem!important;font-weight:750!important;line-height:1.3!important}
.aq-stock-banner.available{background:#066b66!important;border:1px solid #19b7af!important;color:#fff!important}
.aq-stock-banner.low{background:#7a4b00!important;border:1px solid #efb43f!important;color:#fff!important}
[data-testid="stMain"] [class*="st-key-seafood-card-"] h4{font-size:1.05rem!important;margin:.15rem 0 0!important;line-height:1.25!important}
[data-testid="stMain"] [class*="st-key-seafood-card-"] [data-testid="stCaptionContainer"] p{font-size:.73rem!important;margin:0!important}
[data-testid="stMain"] [class*="st-key-seafood-card-"] .stNumberInput{min-width:0!important}
[data-testid="stMain"] [class*="st-key-seafood-card-"] .stNumberInput [data-baseweb="input"]{min-height:38px!important}
[data-testid="stMain"] [class*="st-key-seafood-card-"] .stNumberInput [data-baseweb="input"] input,
[data-testid="stMain"] [class*="st-key-seafood-card-"] .stNumberInput [data-baseweb="input"] button{height:38px!important}
[data-testid="stMain"] [class*="st-key-seafood-card-"] [data-testid="stFormSubmitButton"]{margin-top:.42rem!important}
[data-testid="stMain"] [class*="st-key-seafood-card-"] [data-testid="stFormSubmitButton"] button{min-height:40px!important;font-size:.86rem!important}
[data-testid="stMain"] [class*="st-key-seafood-card-"] [data-testid="stCaptionContainer"]{margin-top:.18rem!important}
@media(max-width:900px){[data-testid="stMain"] [class*="st-key-seafood-card-"] .aq-seafood-card-image img{max-height:190px!important}}
</style>
""")
page_header(
    "Order Seafood",
    "Browse available seafood, prepare your order and review the total before continuing to payment.",
    "Customer Ordering",
)

if "cart" not in st.session_state:
    st.session_state.cart = {}


def available_products(search, category):
    """Always load current catalogue details, including staff-updated descriptions."""
    return [
        product for product in list_products(search, category, "Available")
        if float(product.get("stock_quantity") or 0) >= MIN_WHOLESALE_ORDER_KG
    ]


def _change_cart_quantity(product_id):
    """Apply a cart quantity immediately when its number field changes."""
    quantity = float(st.session_state[f"cart_popover_quantity_{product_id}"])
    if quantity >= MIN_WHOLESALE_ORDER_KG:
        st.session_state.cart[product_id] = quantity
        st.session_state[f"cart_quantity_{product_id}"] = quantity


def _add_product_to_cart(product_id):
    """Save a product-card quantity before the cart popover is rendered."""
    quantity = float(st.session_state[f"cart_quantity_{product_id}"])
    if quantity >= MIN_WHOLESALE_ORDER_KG:
        st.session_state.cart[product_id] = quantity
        st.session_state[f"cart_popover_quantity_{product_id}"] = quantity


@st.fragment
def ordering_workspace():
    """Keep catalogue interactions local and responsive without timed reruns."""
    f1, f2, f3 = st.columns([2, 1, 0.55])
    with f1:
        search = st.text_input("Search Seafood", placeholder="Search by seafood name")
    with f2:
        category = st.selectbox("Category", ["All"] + SEAFOOD_CATEGORIES)
    with f3:
        cart_summary = checkout_summary(list(st.session_state.cart.items()))
        cart_count = len(cart_summary["items"])
        with st.popover(
            f"Cart ({cart_count})", icon=":material/shopping_cart:",
            help="Review items in your cart", use_container_width=True,
        ):
            st.subheader(":material/shopping_cart: Your Cart", anchor=False)
            if not cart_summary["items"]:
                st.info("Your cart is empty. Add seafood to begin.")
            else:
                for line in cart_summary["items"]:
                    st.write(f"**{line['product_name']}**")
                    st.caption(f"RM {line['unit_price']:,.2f} / {line['unit']} · Available: {line['stock_quantity']:g} {line['unit']}")
                    quantity_col, remove_col = st.columns([5, 0.7])
                    with quantity_col:
                        st.number_input(
                            f"Quantity for {line['product_name']} ({line['unit']}, minimum {MIN_WHOLESALE_ORDER_KG:g})",
                            min_value=MIN_WHOLESALE_ORDER_KG,
                            max_value=max(MIN_WHOLESALE_ORDER_KG, float(line["stock_quantity"])),
                            value=max(MIN_WHOLESALE_ORDER_KG, min(float(line["quantity"]), float(line["stock_quantity"]))),
                            step=1.0,
                            key=f"cart_popover_quantity_{line['product_id']}",
                            on_change=_change_cart_quantity,
                            args=(line["product_id"],),
                        )
                    with remove_col:
                        remove_item = st.button(
                            ":material/delete:",
                            key=f"remove_cart_item_{line['product_id']}",
                            help=f"Remove {line['product_name']} from your cart",
                            type="tertiary",
                        )
                    if remove_item:
                        st.session_state.cart.pop(line["product_id"], None)
                        st.session_state.pop(f"cart_popover_quantity_{line['product_id']}", None)
                        st.session_state.pop(f"cart_quantity_{line['product_id']}", None)
                        st.toast(f"{line['product_name']} removed from cart.")
                        st.rerun(scope="fragment")
                st.divider()
                st.write(f"**Total weight:** {cart_summary['total_weight_kg']:g} kg")
                st.markdown(f"### Total: RM {cart_summary['total_amount']:,.2f}")
                if st.button("Proceed to Payment", type="primary", use_container_width=True, key="cart_proceed_payment"):
                    invalid = [
                        line for line in cart_summary["items"]
                        if line["availability_status"] != "Available"
                        or line["quantity"] < MIN_WHOLESALE_ORDER_KG
                        or line["quantity"] > line["stock_quantity"] + 1e-9
                    ]
                    if invalid:
                        st.error("One or more cart items are no longer available. Update the item before payment.")
                    else:
                        st.session_state.checkout_cart = list(st.session_state.cart.items())
                        st.switch_page("pages/payment.py")
    products = available_products(search, category)
    if not products:
        st.info("No seafood with available stock matches your filters.")
    else:
        columns = st.columns(4, gap="small")
        for index, product in enumerate(products):
            with columns[index % 4]:
                with st.container(border=True, key=f"seafood-card-{product['product_id']}"):
                        st.html(seafood_card_image(product, PROJECT_DIR, height=160))
                        st.markdown(f"#### {product['product_name']}")
                        st.caption(f"{product['category']} · Sold by {product['unit']}")
                        st.html(
                            f'<p class="aq-product-description">{escape(product.get("description") or "Available seafood product.")}</p>'
                        )
                        st.html(
                            f'<p class="aq-product-price">RM {float(product.get("unit_price") or 0):,.2f} / {product["unit"]}</p>'
                        )
                        stock = float(product.get("stock_quantity") or 0)
                        if stock <= LOW_STOCK_THRESHOLD:
                            st.html(f'<p class="aq-stock-banner low">Low stock: {stock:g} {product["unit"]} available</p>')
                        else:
                            st.html(f'<p class="aq-stock-banner available">In stock: {stock:g} {product["unit"]} available</p>')
                        current_quantity = min(
                            max(float(st.session_state.cart.get(product["product_id"], 0)), MIN_WHOLESALE_ORDER_KG), stock
                        )
                        with st.form(f"cart_item_{product['product_id']}", border=False):
                            quantity = st.number_input(
                                f"Quantity ({product['unit']})", min_value=MIN_WHOLESALE_ORDER_KG, max_value=stock,
                                step=1.0, value=current_quantity,
                                key=f"cart_quantity_{product['product_id']}",
                            )
                            st.caption(f"Minimum order: {MIN_WHOLESALE_ORDER_KG:g} {product['unit']}")
                            saved = st.form_submit_button(
                                "Add to Cart", icon=":material/add_shopping_cart:",
                                type="primary", use_container_width=True,
                                on_click=_add_product_to_cart,
                                args=(product["product_id"],),
                            )
                        if saved:
                            if quantity < MIN_WHOLESALE_ORDER_KG:
                                st.error(f"Minimum wholesale quantity is {MIN_WHOLESALE_ORDER_KG:g} kg for each seafood product.")
                            else:
                                message = "added to cart." if current_quantity <= 0 else "cart quantity changed."
                                st.toast(f"{product['product_name']} {message}")


ordering_workspace()
st.stop()

f1, f2 = st.columns([2, 1])
with f1:
    search = st.text_input("Search Seafood", placeholder="Search by seafood name")
with f2:
    category = st.selectbox("Category", ["All"] + product_categories())

products = list_products(search, category, "Available")
if "cart" not in st.session_state:
    st.session_state.cart = {}

left, right = st.columns([2.1, 1], gap="large")
with left:
    if not products:
        st.info("No seafood with available stock matches your filters.")
    else:
        cols = st.columns(2)
        for i, product in enumerate(products):
            with cols[i % 2]:
                with st.container(border=True, key=f"seafood-card-{product['product_id']}"):
                    st.html(seafood_card_image(product, PROJECT_DIR))

                    st.markdown(f"### 🐟 {product['product_name']}")
                    st.caption(f"{product['category']} · Sold by {product['unit']}")
                    st.caption("Seafood description")
                    st.write(product.get("description") or "Available seafood product.")
                    st.markdown(f"**RM {float(product.get('unit_price') or 0):,.2f} / {product['unit']}**")

                    stock = float(product.get("stock_quantity") or 0)
                    if stock <= LOW_STOCK_THRESHOLD:
                        st.warning(f"Low stock: {stock:g} {product['unit']} available")
                    else:
                        st.success(f"Available stock: {stock:g} {product['unit']}")

                    current = min(float(st.session_state.cart.get(product["product_id"], 0)), stock)
                    qty = st.number_input(
                        f"Quantity ({product['unit']})",
                        min_value=0.0,
                        max_value=float(stock),
                        step=1.0,
                        value=current,
                        key=f"qty_{product['product_id']}",
                    )

                    if st.button("Add / Update Order", use_container_width=True, key=f"add_{product['product_id']}"):
                        if qty > 0:
                            st.session_state.cart[product["product_id"]] = qty
                            st.success("Order selection updated.")
                        else:
                            st.session_state.cart.pop(product["product_id"], None)
                            st.info("Item removed from order selection.")

with right:
    st.subheader("Order Summary", anchor=False)
    summary = checkout_summary(list(st.session_state.cart.items()))

    if not summary["items"]:
        st.info("No seafood selected yet.")
    else:
        for line in summary["items"]:
            st.write(f"**{line['product_name']}**")
            st.caption(
                f"{line['quantity']:g} {line['unit']} × RM {line['unit_price']:,.2f} "
                f"= RM {line['line_total']:,.2f}"
            )

        st.divider()
        st.write(f"**Total Seafood Weight:** {summary['total_weight_kg']:g} kg")
        st.markdown(f"### Total: RM {summary['total_amount']:,.2f}")
        st.caption(
            "Your wholesale collection point will be assigned automatically from your registered location after checkout."
        )

        if st.button("Proceed to Payment", type="primary", use_container_width=True):
            invalid = [
                line
                for line in summary["items"]
                if line["availability_status"] != "Available"
                or line["quantity"] > line["stock_quantity"] + 1e-9
            ]
            if invalid:
                st.error("One or more seafood quantities are no longer available. Please update your selection.")
            else:
                st.session_state.checkout_cart = list(st.session_state.cart.items())
                st.switch_page("pages/payment.py")
