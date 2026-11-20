import sys
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.theme import apply_theme, page_header
from components.navigation import customer_sidebar
from services.order_service import get_order
from services.payment_service import payment_status_label

bootstrap_app()
st.set_page_config(page_title="Order Confirmed | AquaLoad", page_icon="✅", layout="wide")
apply_theme(); customer_sidebar()

order_id = st.session_state.get("last_paid_order_id")
order = get_order(order_id, st.session_state.user_id) if order_id else None

page_header(
    "Order Placed",
    "Your seafood order has been placed and is now waiting for Staff review.",
    "Order Confirmation",
)

if not order:
    st.info("No recently completed checkout was found.")
    if st.button("View My Orders", type="primary"):
        st.switch_page("pages/my_orders.py")
    st.stop()

st.success("Order placed successfully.")
payment = order.get("payment") or {}
with st.container(border=True):
    st.markdown("## ✓ Order Placed Successfully")
    a, b, c, d = st.columns(4)
    a.metric("Order", f"#{order['order_id']}")
    b.metric("Order total", f"RM {float(payment.get('amount') or order.get('total_amount') or 0):,.2f}")
    c.metric("Payment", payment_status_label(payment.get("payment_status")))
    d.metric("Order Status", order["status"])

    st.divider()
    if payment.get("payment_status") in {"Simulated", "Demo Refund Pending", "Refund Pending"}:
        st.caption("Payment simulation only; no actual money was transferred.")
    st.write(f"**Payment Method:** {payment.get('payment_method') or '—'}")
    st.write(f"**Payment Reference:** {payment.get('transaction_reference') or '—'}")
    st.write(f"**Total Seafood Weight:** {float(order.get('total_weight_kg') or 0):g} kg")
    st.write(
        f"**Collection Point:** {order.get('collection_point_name') or order.get('collection_point') or 'Not assigned'}"
    )
    if order.get("collection_assignment") == "Local Pickup":
        st.info("Your order is a Perlis self-pickup order and will not be assigned to a lorry.")
    else:
        st.caption("Staff will manually update the operational order status as the order is prepared, loaded and completed.")

c1, c2 = st.columns(2)
with c1:
    if st.button("View My Orders", type="primary", use_container_width=True):
        st.switch_page("pages/my_orders.py")
with c2:
    if st.button("Track Order", use_container_width=True):
        st.session_state.selected_order_id = order["order_id"]
        st.switch_page("pages/track_order.py")
