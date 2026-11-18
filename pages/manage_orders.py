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
from constants import ORDER_STATUSES
from services.box_service import list_box_inventory
from services.order_service import (
    list_all_orders,
    get_order,
    order_counts,
    recommend_box_combinations,
    accept_box_recommendation,
    box_requirement_shortage_message,
    set_manual_box_requirements,
)

bootstrap_app()
st.set_page_config(page_title="Customer Orders | AquaLoad", page_icon="📋", layout="wide")
apply_theme(); staff_sidebar(); require_staff()


def _show_page_feedback(order_id):
    """Show the latest action result once for the order that triggered it."""
    message = st.session_state.pop("manage_orders_feedback", None)
    if message and len(message) == 3 and message[0] == order_id:
        getattr(st, message[1])(message[2])


def _accept_recommendation(order_id):
    """Save the recommended boxes for a paid pending order."""
    current = get_order(order_id)
    if not current:
        return False, "This order is no longer available. Refresh the page and try again."
    if current["status"] != "Ready for Loading":
        return False, f"Only Ready for Loading orders can accept a box recommendation. This order is {current['status']}."
    if (current.get("payment") or {}).get("payment_status") not in {"Paid", "Simulated"}:
        return False, "A successful payment is required before saving the box requirement."
    if not current.get("collection_point_id"):
        return False, "The customer must choose a collection point during payment before box requirements can be saved."

    return accept_box_recommendation(order_id, 0)


page_header(
    "Customer Order Management",
    "Review customer orders and prepare standardized box requirements before loading.",
    "Seafood & Orders",
)

counts = order_counts()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Active Orders", counts["active"])
c2.metric("Pending Review", counts["pending"])
c3.metric("Ready for Loading", counts["ready"])
c4.metric("Completed", counts["completed"])

f1, f2 = st.columns([2, 1])
with f1:
    search = st.text_input("Search Order", placeholder="Order ID, Customer name or email")
with f2:
    status = st.selectbox("Status", ["All"] + ORDER_STATUSES)
view_mode = st.radio(
    "Order Records",
    ["Current Orders", "Archived Orders"],
    horizontal=True,
    key="manage_orders_record_filter",
)
orders = list_all_orders(status, search, archived_only=view_mode == "Archived Orders")
archived_view = view_mode == "Archived Orders"

if not orders:
    st.info("No Customer orders match the selected filters.")
    st.stop()

summary_rows = [{
    "Order": f"#{o['order_id']}",
    "Customer": o["customer_name"],
    "Customer Location": f"{o.get('customer_city') or '—'}, {o.get('customer_state') or '—'}",
    "Status": o["status"],
    "Total Seafood Weight": f"{float(o['total_weight_kg']):g} kg",
    "Payment": o.get("payment_status") or "Not Paid",
    "Order Amount": f"RM {float(o.get('order_total_amount') or 0):,.2f}",
    "Collection Point": o.get("collection_point") or "Not assigned",
    "Updated": friendly_datetime(o["updated_at"]),
} for o in orders]
st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

st.subheader("Archived Order Details" if archived_view else "Order Details & Actions", anchor=False)
order_map = {f"Order #{o['order_id']} · {o['customer_name']} · {float(o['total_weight_kg']):g} kg": o["order_id"] for o in orders}
selected_order_id = order_map[st.selectbox("Select Order", list(order_map))]
order = get_order(selected_order_id)

left, right = st.columns([1, 1.15], gap="large")

with left:
    with st.container(border=True):
        st.markdown(f"### Order #{order['order_id']}")
        st.write(f"**Customer:** {order['customer_name']} ({order['customer_email']})")
        st.write(f"**Customer Location:** {order.get('customer_city') or '—'}, {order.get('customer_state') or '—'}")
        st.write(f"**Current Status:** {order['status']}")
        payment = order.get("payment") or {}
        st.write(f"**Payment:** {payment.get('payment_status') or 'Not Paid'} · RM {float(payment.get('amount') or order.get('total_amount') or 0):,.2f}")
        st.write(f"**Collection Point:** {order.get('collection_point_name') or order.get('collection_point') or 'Not assigned'}")
        st.markdown("#### Items")
        for item in order["items"]:
            st.write(f"• {item['product_name']}: {float(item['quantity']):g} {item['unit']}")
        st.divider()
        st.markdown(f"### Total Order Weight: {float(order['total_weight_kg']):g} kg")
        st.markdown("#### Status History")
        for h in order["history"]:
            note = f" — {h['note']}" if h.get("note") else ""
            st.caption(f"{friendly_datetime(h['updated_at'])} · {h['status']} · {h['updated_by_name']}{note}")

if archived_view:
    with right:
        with st.container(border=True):
            st.markdown("### Archived Record")
            st.info("This order is archived and read-only.")
            st.write(f"**Archived on:** {friendly_datetime(order.get('archived_at'), 'Recorded in the archive')}")
            st.write("Collection point, box requirements, payment, and status history are retained in this record.")
    st.stop()

with right:
    with st.container(border=True):
        st.markdown("### Box Requirements")
        _show_page_feedback(order["order_id"])
        st.markdown("### Recommended Box Requirement")
        total_weight = float(order["total_weight_kg"])
        st.metric("Total Seafood Weight", f"{total_weight:g} kg")
        recommendations = recommend_box_combinations(order["order_id"], limit=3)

        if recommendations:
            best = recommendations[0]
            for box in best["boxes"]:
                st.write(
                    f"**{box['quantity']} × {box['capacity_litre']}L** — {box['dimensions']} · "
                    f"{box['capacity_per_box_kg']:g} kg max each"
                )
            st.write(f"**Total capacity:** {best['total_capacity_kg']:g} kg")
            st.write(f"**Unused capacity:** {best['unused_capacity_kg']:g} kg")

            if st.button(
                "Accept Recommendation",
                type="primary",
                use_container_width=True,
            ):
                ok, msg = _accept_recommendation(order["order_id"])
                if ok:
                    st.session_state.manage_orders_feedback = (order["order_id"], "success", msg)
                    st.rerun()
                else:
                    st.error(msg)

            if len(recommendations) > 1:
                with st.expander("View Alternative Box Combinations"):
                    for idx, rec in enumerate(recommendations[1:], start=2):
                        desc = " + ".join(f"{b['quantity']} × {b['capacity_litre']}L" for b in rec["boxes"])
                        st.write(f"**Alternative {idx - 1}:** {desc}")
                        st.caption(
                            f"{rec['box_count']} boxes · {rec['total_capacity_kg']:g} kg capacity · {rec['unused_capacity_kg']:g} kg unused"
                        )
        else:
            st.error(box_requirement_shortage_message(order["order_id"]))

        with st.expander("Adjust Box Requirement Manually"):
            st.caption("Manual selections still must provide enough capacity and cannot exceed available box inventory.")
            inventory = list_box_inventory(exclude_order_id=order["order_id"])
            selections = []
            # Keep quantity changes in the browser until Staff explicitly
            # saves. This avoids a full rerun and inventory query on each +/-.
            with st.form(f"manual_box_requirement_{order['order_id']}", border=False):
                cols = st.columns(2)
                for i, box in enumerate(inventory):
                    with cols[i % 2]:
                        qty = st.number_input(
                            f"{int(box['capacity_litre'])}L quantity",
                            min_value=0,
                            max_value=int(box["available_quantity"]),
                            value=0,
                            step=1,
                            key=f"manual_box_{order['order_id']}_{box['box_profile_id']}",
                            help=f"Fixed size {box['length']:g} × {box['width']:g} × {box['height']:g} cm; max {box['max_seafood_weight_kg']:g} kg each; available {box['available_quantity']}.",
                        )
                        selections.append((box["box_profile_id"], qty))
                save_manual = st.form_submit_button(
                    "Save Manual Box Requirement", type="primary", use_container_width=True
                )
            if save_manual:
                ok, msg = set_manual_box_requirements(order["order_id"], selections)
                if ok:
                    st.session_state.manage_orders_feedback = (order["order_id"], "success", msg)
                    st.rerun()
                else:
                    st.error(msg)

        st.markdown("#### Current Requirement")
        if not order["box_requirements"]:
            st.caption("No box requirement has been saved yet.")
        else:
            for req in order["box_requirements"]:
                st.write(
                    f"• {req['quantity']} × {int(req['capacity_litre'])}L "
                    f"({req['length']:g} × {req['width']:g} × {req['height']:g} cm), "
                    f"~{req['loaded_weight_per_box']:.1f} kg loaded per box"
                )
