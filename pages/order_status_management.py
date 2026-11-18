import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.theme import apply_theme, page_header
from components.display import friendly_datetime
from components.navigation import staff_sidebar, require_staff
from components.feedback import flash
from services.order_service import list_all_orders, get_order, allowed_next_statuses, update_order_status

bootstrap_app()
st.set_page_config(page_title="Order Status | AquaLoad", page_icon="🔄", layout="wide")
apply_theme(); staff_sidebar(); require_staff()
page_header(
    "Order Status & Tracking Management",
    "Update each real operational stage manually and review the complete status history.",
    "Seafood & Orders",
)

orders = list_all_orders()
if not orders:
    st.info("No orders are available.")
    st.stop()

rows = [{
    "Order": f"#{o['order_id']}",
    "Customer": o["customer_name"],
    "Current Status": o["status"],
    "Weight": f"{float(o['total_weight_kg']):g} kg",
    "Collection Point": o.get("collection_point") or "Not assigned",
    "Last Updated": friendly_datetime(o["updated_at"]),
} for o in orders]
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

order_map = {f"Order #{o['order_id']} · {o['customer_name']} · {o['status']}": o["order_id"] for o in orders}
order_id = order_map[st.selectbox("Select Order", list(order_map))]
order = get_order(order_id)

left, right = st.columns([1, 1], gap="large")
with left:
    with st.container(border=True):
        st.markdown(f"### Order #{order_id}")
        st.write(f"**Current Status:** {order['status']}")
        st.write(f"**Collection Point:** {order.get('collection_point_name') or order.get('collection_point') or 'Not assigned'}")
        st.write(f"**Total Seafood Weight:** {order['total_weight_kg']:g} kg")
        next_statuses = allowed_next_statuses(order["status"])
        if next_statuses:
            next_status = st.selectbox("Next Status", next_statuses)
            note = st.text_input("Operational Note", placeholder="Example: Physical loading completed")
            if st.button("Confirm Status Update", type="primary", use_container_width=True):
                ok, msg = update_order_status(order_id, next_status, st.session_state.user_id, note)
                if ok:
                    flash("success", msg)
                    st.rerun()
                else:
                    st.error(msg, icon="⚠️")
        else:
            st.info("This order has reached a final status.")

with right:
    with st.container(border=True):
        st.markdown("### Tracking Records")
        for idx, h in enumerate(order["history"], start=1):
            st.markdown(f"**{idx}. {h['status']}**")
            st.caption(f"{friendly_datetime(h['updated_at'])} · {h['updated_by_name']}")
            if h.get("note"):
                st.write(h["note"])
            if idx != len(order["history"]):
                st.divider()
