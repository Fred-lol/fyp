import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.theme import apply_theme, page_header
from components.tables import render_dataframe
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
    box_requirement_capacity,
    set_manual_box_requirements,
)
from services.payment_service import payment_status_label

bootstrap_app()
st.set_page_config(page_title="Customer Orders | AquaLoad", page_icon="📋", layout="wide")
apply_theme(); staff_sidebar(); require_staff()


def _show_page_feedback(order_id):
    """Show the latest action result once for the order that triggered it."""
    message = st.session_state.pop("manage_orders_feedback", None)
    if message and len(message) == 3 and message[0] == order_id:
        getattr(st, message[1])(message[2])


def _accept_recommendation(order_id):
    """Save a validated recommendation and advance a confirmed delivery order."""
    current = get_order(order_id)
    if not current:
        return False, "This order is no longer available. Refresh the page and try again."
    if current["status"] not in {"Confirmed", "Ready for Loading"}:
        return False, f"Confirm the order before saving its box requirement. This order is {current['status']}."
    if (current.get("payment") or {}).get("payment_status") not in {"Paid", "Simulated"}:
        return False, "A successful payment is required before saving the box requirement."
    if not current.get("collection_point_id"):
        return False, "The customer must choose a collection point during payment before box requirements can be saved."
    if current.get("collection_assignment") == "Local Pickup":
        return False, "Local pickup orders do not need boxes or lorry loading."

    return accept_box_recommendation(order_id, 0, st.session_state.user_id)


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
    "Payment": payment_status_label(o.get("payment_status")),
    "Order Amount": f"RM {float(o.get('order_total_amount') or 0):,.2f}",
    "Collection Point": o.get("collection_point") or "Not assigned",
    "Updated": friendly_datetime(o["updated_at"]),
} for o in orders]
render_dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

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
        st.write(f"**Payment status:** {payment_status_label(payment.get('payment_status'))} · RM {float(payment.get('amount') or order.get('total_amount') or 0):,.2f}")
        if payment.get("payment_status") in {"Simulated", "Demo Refund Pending", "Refund Pending"}:
            st.caption("Payment simulation only; no actual money was transferred.")
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
            st.caption("Manual selections recalculate seafood capacity immediately. Quantities cannot exceed available box inventory.")
            inventory = list_box_inventory(exclude_order_id=order["order_id"])
            selections = []
            current_quantities = {
                int(req["box_profile_id"]): int(req["quantity"])
                for req in order.get("box_requirements", [])
            }
            if not inventory:
                st.error("No active box inventory is available for this order.")
            cols = st.columns(2)
            for i, box in enumerate(inventory):
                with cols[i % 2]:
                    qty = st.number_input(
                        f"{int(box['capacity_litre'])}L quantity",
                        min_value=0,
                        max_value=int(box["available_quantity"]),
                        value=min(current_quantities.get(int(box["box_profile_id"]), 0), int(box["available_quantity"])),
                        step=1,
                        key=f"manual_box_{order['order_id']}_{box['box_profile_id']}",
                        help=f"Fixed internal dimensions: {box['length']:g} x {box['width']:g} x {box['height']:g} cm; max {box['max_seafood_weight_kg']:g} kg seafood per box; {box['available_quantity']} available.",
                    )
                    selections.append((box["box_profile_id"], qty))

            selected_boxes = [
                {
                    "capacity_per_box_kg": float(box["max_seafood_weight_kg"] or 0),
                    "quantity": int(qty),
                }
                for box in inventory
                for profile_id, qty in selections
                if int(profile_id) == int(box["box_profile_id"]) and int(qty) > 0
            ]
            selected_capacity, remaining_kg, unused_capacity = box_requirement_capacity(total_weight, selected_boxes)
            capacity_col, remaining_col = st.columns(2)
            capacity_col.metric("Selected Box Capacity", f"{selected_capacity:g} kg")
            remaining_col.metric("Remaining Seafood", f"{remaining_kg:g} kg")
            capacity_sufficient = bool(selected_boxes) and remaining_kg <= 1e-9
            if capacity_sufficient:
                st.success("Box capacity is sufficient.")
                st.caption(f"Unused box capacity: {unused_capacity:g} kg.")
            else:
                st.error(
                    f"Insufficient box capacity. {remaining_kg:g} kg of seafood still requires box capacity."
                )

            save_manual = st.button(
                "Save Manual Box Requirement",
                type="primary",
                use_container_width=True,
                disabled=not capacity_sufficient,
                key=f"save_manual_box_requirement_{order['order_id']}",
            )
            if save_manual:
                ok, msg = set_manual_box_requirements(
                    order["order_id"], selections, st.session_state.user_id
                )
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
