import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.theme import apply_theme, page_header
from components.navigation import customer_sidebar
from components.cards import metric_card, empty_state
from services.order_service import list_customer_orders

bootstrap_app()

st.set_page_config(
    page_title="Customer Dashboard | AquaLoad",
    page_icon="🐟",
    layout="wide",
)
apply_theme()
customer_sidebar()

name = st.session_state.get("user_name", "Customer")
page_header(
    f"Welcome back, {name}",
    "Order seafood and keep track of your latest orders.",
    "Customer Dashboard",
)

orders = list_customer_orders(st.session_state.user_id)
active = [o for o in orders if o["status"] not in {"Completed", "Cancelled"}]
latest = orders[0] if orders else None

c1, c2, c3 = st.columns(3)
with c1:
    metric_card("Active Orders", len(active), "Orders still in progress")
with c2:
    metric_card(
        "Latest Order",
        f"#{latest['order_id']}" if latest else "—",
        latest["status"] if latest else "No order yet",
    )
with c3:
    metric_card("Total Orders", len(orders), "All seafood orders")

st.write("")
q1, q2, q3 = st.columns(3)
with q1:
    if st.button("Order Seafood", icon=":material/set_meal:", type="primary", use_container_width=True):
        st.switch_page("pages/order_seafood.py")
with q2:
    if st.button("View My Orders", icon=":material/receipt_long:", use_container_width=True):
        st.switch_page("pages/my_orders.py")
with q3:
    if st.button("Track Order", icon=":material/location_on:", use_container_width=True):
        st.switch_page("pages/track_order.py")

st.subheader("Recent Orders", anchor=False)
if not orders:
    empty_state("You have not placed any seafood orders yet.")
else:
    # list_customer_orders() returns total_weight_kg, not total_quantity.
    # Build the display table from the service fields so the dashboard stays
    # consistent with My Orders and the box recommendation logic.
    rows = []
    for order in orders[:5]:
        rows.append(
            {
                "Order": f"#{order['order_id']}",
                "Order Date": order["order_date"],
                "Items": int(order.get("item_count") or 0),
                "Total Weight": f"{float(order.get('total_weight_kg') or 0):g} kg",
                "Payment": order.get("payment_status") or "Not Paid",
                "Status": order["status"],
            }
        )

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )
