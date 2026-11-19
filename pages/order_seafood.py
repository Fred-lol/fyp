"""Customer seafood catalogue and cart workspace."""

import sys
from html import escape
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.cards import empty_cart
from components.navigation import customer_sidebar, require_role
from components.commerce import COMMERCE_CSS, product_card, product_details
from components.theme import apply_theme, page_header
from constants import MIN_WHOLESALE_ORDER_KG
from services.order_service import list_products, product_categories
from services.product_service import get_product
from services.favorites_service import list_favorite_product_ids, set_favorite
from services.payment_service import checkout_summary
from constants import ROLES


bootstrap_app()
st.set_page_config(page_title="Order Seafood | AquaLoad", page_icon="🐟", layout="wide")
apply_theme()
customer_sidebar()

st.html(COMMERCE_CSS)

page_header("Order Seafood", "Browse the current wholesale catalogue, add items to your cart, then review payment.", "Customer Ordering")

if "cart" not in st.session_state:
    st.session_state.cart = {}


def _catalogue_products(search: str, category: str) -> list[dict]:
    """Return only seafood that a customer can order right now.

    Products marked Unavailable, out of stock, or below AquaLoad's 10 kg
    wholesale minimum remain hidden until staff replenishes and enables them.
    """
    return [
        product
        for product in list_products(search, category, "Available")
        if float(product.get("stock_quantity") or 0) >= MIN_WHOLESALE_ORDER_KG
    ]


def _change_cart_quantity(product_id: int) -> None:
    quantity = float(st.session_state[f"cart_popover_quantity_{product_id}"])
    if _cart_quantity_available(product_id, quantity):
        st.session_state.cart[product_id] = quantity
        st.session_state[f"cart_quantity_{product_id}"] = quantity


def _add_product_to_cart(product_id: int, product_name: str) -> None:
    quantity = float(st.session_state[f"cart_quantity_{product_id}"])
    if _cart_quantity_available(product_id, quantity):
        verb = "quantity updated" if product_id in st.session_state.cart else "added to cart"
        st.session_state.catalogue_feedback = f"{product_name} {verb}."
        st.session_state.cart[product_id] = quantity
        st.session_state[f"cart_popover_quantity_{product_id}"] = quantity
        st.session_state.pop("selected_seafood_id", None)


def _open_product_details(product_id: int) -> None:
    st.session_state.selected_seafood_id = product_id


def _back_to_catalogue() -> None:
    st.session_state.pop("selected_seafood_id", None)


def _toggle_favorite(product_id: int) -> None:
    """Persist a favorite and update this customer's current session view."""
    favorites = set(st.session_state.get("favorite_product_ids", set()))
    favorite = int(product_id) not in favorites
    ok, message = set_favorite(st.session_state.user_id, int(product_id), favorite)
    if ok:
        if favorite:
            favorites.add(int(product_id))
        else:
            favorites.discard(int(product_id))
        st.session_state.favorite_product_ids = favorites
        st.session_state.catalogue_feedback = message
    else:
        st.session_state.catalogue_error = message


def _cart_quantity_available(product_id, quantity):
    """Recheck stock at the action boundary, without fetching product images."""
    from math import isfinite
    if not isfinite(quantity) or quantity < MIN_WHOLESALE_ORDER_KG:
        st.session_state.catalogue_error = f"Choose at least {MIN_WHOLESALE_ORDER_KG:g} kg."
        return False
    lines = checkout_summary([(product_id, quantity)])["items"]
    if not lines or lines[0]["availability_status"] != "Available":
        st.session_state.catalogue_error = "This seafood is no longer available."
        return False
    if quantity > lines[0]["stock_quantity"]:
        st.session_state.catalogue_error = f"Only {lines[0]['stock_quantity']:g} kg of {lines[0]['product_name']} remains. Reduce the quantity."
        return False
    return True


@st.fragment
def ordering_workspace() -> None:
    # Fragment interactions repeat only this section. Recheck authorization
    # here too, so an expired/cleared session never exposes the detail panel.
    require_role(ROLES["CUSTOMER"])
    filters, category_filter, favorites_filter, cart_action = st.columns([2.1, 1, .85, .58], vertical_alignment="bottom")
    with filters:
        search = st.text_input("Search seafood", placeholder="Search by seafood name", key="catalogue_search")
    with category_filter:
        category = st.selectbox("Category", ["All"] + product_categories(), key="catalogue_category")
    with favorites_filter:
        favorites_only = st.checkbox("Favorites only", key="catalogue_favorites_only")
    with cart_action:
        cart_summary = checkout_summary(list(st.session_state.cart.items()))
        with st.popover(f"Cart ({len(cart_summary['items'])})", icon=":material/shopping_cart:", help="Review cart", use_container_width=True):
            with st.container(key="cart_panel"):
                st.subheader("Your Cart", anchor=False)
                if not cart_summary["items"]:
                    empty_cart()
                else:
                    for line in cart_summary["items"]:
                        with st.container(key=f"cart_line_{line['product_id']}"):
                            st.html(f'<div class="aq-cart-line-title"><strong>{escape(line["product_name"])}</strong><strong>RM {line["line_total"]:,.2f}</strong></div>')
                            st.caption(f"RM {line['unit_price']:,.2f} / {line['unit']} · {line['quantity']:g} {line['unit']} · Subtotal RM {line['line_total']:,.2f}")
                            quantity_col, remove_col = st.columns([5, .75], vertical_alignment="bottom")
                            with quantity_col:
                                quantity_key = f"cart_popover_quantity_{line['product_id']}"
                                if quantity_key not in st.session_state:
                                    st.session_state[quantity_key] = max(
                                        MIN_WHOLESALE_ORDER_KG,
                                        min(float(line["quantity"]), float(line["stock_quantity"])),
                                    )
                                st.number_input(
                                    f"Quantity for {line['product_name']} ({line['unit']})", min_value=MIN_WHOLESALE_ORDER_KG,
                                    max_value=max(MIN_WHOLESALE_ORDER_KG, float(line["stock_quantity"])),
                                    step=1.0, key=quantity_key,
                                    on_change=_change_cart_quantity, args=(line["product_id"],),
                                )
                            with remove_col:
                                if st.button(":material/delete:", key=f"remove_cart_item_{line['product_id']}", help=f"Remove {line['product_name']} from cart", type="tertiary"):
                                    st.session_state.cart.pop(line["product_id"], None)
                                    st.session_state.pop(f"cart_popover_quantity_{line['product_id']}", None)
                                    st.session_state.pop(f"cart_quantity_{line['product_id']}", None)
                                    st.session_state.catalogue_feedback = f"{line['product_name']} removed from cart."
                                    st.rerun(scope="fragment")
                    st.html(f"""<div class="aq-cart-totals"><strong>Total seafood weight</strong><div>{cart_summary['total_weight_kg']:g} kg</div><div class="aq-cart-total-amount">RM {cart_summary['total_amount']:,.2f}</div></div>""")
                    if st.button("Proceed to payment", type="primary", use_container_width=True, key="cart_proceed_payment"):
                        invalid = [line for line in cart_summary["items"] if line["availability_status"] != "Available" or line["quantity"] < MIN_WHOLESALE_ORDER_KG or line["quantity"] > line["stock_quantity"] + 1e-9]
                        if invalid:
                            st.error("One or more cart items are no longer available. Review their quantity before payment.")
                        else:
                            st.session_state.checkout_cart = list(st.session_state.cart.items())
                            st.switch_page("pages/payment.py")

    if message := st.session_state.pop("catalogue_feedback", None):
        st.success(message)
    if message := st.session_state.pop("catalogue_error", None):
        st.error(message)

    selected_id = st.session_state.get("selected_seafood_id")
    if selected_id is not None:
        # Resolve by id instead of searching the filtered card list. This
        # preserves the catalogue filters and keeps navigation inside the
        # same authenticated Streamlit session.
        try:
            selected = get_product(int(selected_id))
        except (TypeError, ValueError):
            selected = None
        if (selected is None or selected.get("availability_status") != "Available"
                or float(selected.get("stock_quantity") or 0) < MIN_WHOLESALE_ORDER_KG):
            st.error("This seafood is no longer available. Return to the catalogue to choose another item.")
            st.button("Back to Catalogue", on_click=_back_to_catalogue, key="back_to_catalogue_unavailable")
            return
        st.button("Back to Catalogue", icon=":material/arrow_back:", on_click=_back_to_catalogue, key="back_to_catalogue")
        product_details(
            selected,
            PROJECT_DIR,
            _add_product_to_cart,
            is_favorite=int(selected_id) in set(st.session_state.get("favorite_product_ids", set())),
            on_favorite=_toggle_favorite,
        )
        return

    products = _catalogue_products(search, category)
    favorite_ids = set(st.session_state.get("favorite_product_ids", set()))
    if favorites_only:
        products = [product for product in products if int(product["product_id"]) in favorite_ids]
    if not products:
        if favorites_only and not favorite_ids:
            st.info("You have not saved any seafood to Favorites yet. Use the heart on a product to save it here.")
        elif favorites_only:
            st.info("No available seafood matches your favorites and current search or category.")
        else:
            st.info("No seafood is currently available for this search or category. Please check again after stock is replenished.")
        return

    with st.container(key="catalogue_grid"):
        for product in products:
            product_card(
                product,
                PROJECT_DIR,
                _open_product_details,
                is_favorite=int(product["product_id"]) in favorite_ids,
                on_favorite=_toggle_favorite,
            )



favorite_owner = st.session_state.get("user_id")
if st.session_state.get("_favorite_owner") != favorite_owner:
    st.session_state.favorite_product_ids = list_favorite_product_ids(favorite_owner)
    st.session_state._favorite_owner = favorite_owner

ordering_workspace()
